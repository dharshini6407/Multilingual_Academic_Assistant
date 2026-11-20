import os
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import db
from models import AcademicDocument, DocumentVersion, DocumentChunk
from services.auth_service import admin_required
from services.pdf_service import extract_text_and_chunks_from_pdf
from config import Config

documents_bp = Blueprint('documents', __name__)

@documents_bp.route('', methods=['GET'])
@jwt_required()
def list_documents():
    """List academic documents. Admins see all; students see active documents only."""
    from models import User
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    is_admin = user and user.role == 'admin'

    if is_admin:
        docs = AcademicDocument.query.order_by(AcademicDocument.created_at.desc()).all()
    else:
        docs = AcademicDocument.query.filter_by(is_active=True).order_by(AcademicDocument.created_at.desc()).all()

    return jsonify({
        'success': True,
        'documents': [d.to_dict() for d in docs]
    }), 200

@documents_bp.route('/upload', methods=['POST'])
@jwt_required()
@admin_required()
def upload_academic_pdf():
    """
    Admin uploads official academic PDF.
    Validates, extracts text, generates structured chunks, and indexes into database.
    """
    user_id = int(get_jwt_identity())

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part in upload request.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file.'}), 400

    filename = secure_filename(file.filename)
    if not filename.lower().endswith('.pdf'):
        return jsonify({'success': False, 'message': 'Invalid file format. Only PDF files are allowed.'}), 400

    title = request.form.get('title', '').strip() or os.path.splitext(filename)[0].replace('_', ' ').title()
    category = request.form.get('category', 'curriculum')
    description = request.form.get('description', '')
    language = request.form.get('language', 'en')

    # Ensure uploads directory exists
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    save_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(save_path)
    file_size = os.path.getsize(save_path)

    try:
        # Extract and chunk PDF
        extraction_result = extract_text_and_chunks_from_pdf(save_path)
        chunks = extraction_result['chunks']
        total_pages = extraction_result['total_pages']

        # Create or update document record
        doc = AcademicDocument(
            title=title,
            category=category,
            file_name=filename,
            file_path=save_path,
            file_size_bytes=file_size,
            mime_type='application/pdf',
            is_active=True,
            total_pages=total_pages,
            total_chunks=len(chunks),
            language=language,
            description=description,
            created_by=user_id
        )
        db.session.add(doc)
        db.session.flush()

        # Add initial version
        version = DocumentVersion(
            document_id=doc.id,
            version_number=1,
            change_summary='Initial upload and indexing',
            file_path=save_path,
            uploaded_by=user_id
        )
        db.session.add(version)

        # Store chunks
        for c in chunks:
            chunk_rec = DocumentChunk(
                document_id=doc.id,
                chunk_index=c['chunk_index'],
                page_number=c['page_number'],
                section_title=c['section_title'],
                content=c['content'],
                content_length=c['content_length']
            )
            db.session.add(chunk_rec)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Document "{title}" uploaded, parsed, and indexed into {len(chunks)} searchable chunks.',
            'document': doc.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        # Clean up file on failure if needed
        return jsonify({'success': False, 'message': f'PDF processing error: {str(e)}'}), 422

@documents_bp.route('/<int:doc_id>/toggle-status', methods=['PUT'])
@jwt_required()
@admin_required()
def toggle_document_status(doc_id):
    """Admin toggles active/inactive status (inactive docs are excluded from RAG retrieval)."""
    doc = AcademicDocument.query.get(doc_id)
    if not doc:
        return jsonify({'success': False, 'message': 'Document not found.'}), 404

    doc.is_active = not doc.is_active
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Document is now {"active and searchable" if doc.is_active else "inactive (excluded from retrieval)"}.',
        'document': doc.to_dict()
    }), 200

@documents_bp.route('/<int:doc_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_document(doc_id):
    """Admin deletes document (cascades to all chunks and versions)."""
    doc = AcademicDocument.query.get(doc_id)
    if not doc:
        return jsonify({'success': False, 'message': 'Document not found.'}), 404

    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    db.session.delete(doc)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Document and all indexed chunks deleted successfully.'
    }), 200

@documents_bp.route('/reindex', methods=['POST'])
@jwt_required()
@admin_required()
def reindex_all_documents():
    """Admin reindexes all active PDFs in knowledge base."""
    active_docs = AcademicDocument.query.filter_by(is_active=True).all()
    total_reindexed_chunks = 0

    for doc in active_docs:
        if os.path.exists(doc.file_path):
            try:
                extraction = extract_text_and_chunks_from_pdf(doc.file_path)
                # Remove old chunks
                DocumentChunk.query.filter_by(document_id=doc.id).delete()
                # Insert fresh chunks
                for c in extraction['chunks']:
                    chunk_rec = DocumentChunk(
                        document_id=doc.id,
                        chunk_index=c['chunk_index'],
                        page_number=c['page_number'],
                        section_title=c['section_title'],
                        content=c['content'],
                        content_length=c['content_length']
                    )
                    db.session.add(chunk_rec)
                doc.total_chunks = len(extraction['chunks'])
                doc.total_pages = extraction['total_pages']
                total_reindexed_chunks += len(extraction['chunks'])
            except Exception as e:
                current_app.logger.error(f"Error reindexing doc {doc.id}: {e}")

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Reindexing completed. Indexed {total_reindexed_chunks} chunks across {len(active_docs)} active documents.'
    }), 200
