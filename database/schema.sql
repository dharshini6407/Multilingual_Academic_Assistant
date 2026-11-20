-- =====================================================================
-- Multilingual Academic Information Assistant with Smart Academic Alerts
-- and Personalized Study Planning
-- Complete Production Database Schema (MySQL 8.0+)
-- Character set: utf8mb4 (Supports English, Tamil தமிழ், and Tanglish)
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `academic_assistant`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE `academic_assistant`;

-- ---------------------------------------------------------------------
-- 1. USERS & ROLES
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `email` VARCHAR(191) NOT NULL UNIQUE,
  `password_hash` VARCHAR(255) NOT NULL,
  `role` ENUM('student', 'admin') NOT NULL DEFAULT 'student',
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_users_role` (`role`),
  INDEX `idx_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 2. USER PROFILES
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `user_profiles` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL UNIQUE,
  `full_name` VARCHAR(150) NOT NULL,
  `register_number` VARCHAR(50) DEFAULT NULL,
  `department` VARCHAR(100) NOT NULL DEFAULT 'Computer Science and Engineering',
  `year_of_study` INT NOT NULL DEFAULT 3,
  `semester` INT NOT NULL DEFAULT 5,
  `preferred_language` ENUM('en', 'ta', 'tanglish') NOT NULL DEFAULT 'en',
  `avatar_url` VARCHAR(255) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 3. NOTIFICATION PREFERENCES
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `notification_preferences` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL UNIQUE,
  `exam_alerts` BOOLEAN NOT NULL DEFAULT TRUE,
  `assignment_alerts` BOOLEAN NOT NULL DEFAULT TRUE,
  `activity_alerts` BOOLEAN NOT NULL DEFAULT TRUE,
  `low_attendance_warning` BOOLEAN NOT NULL DEFAULT TRUE,
  `study_plan_reminders` BOOLEAN NOT NULL DEFAULT TRUE,
  `preferred_channel` ENUM('in_app', 'email', 'both') NOT NULL DEFAULT 'in_app',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 4. SUBJECTS
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `subjects` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `code` VARCHAR(20) NOT NULL UNIQUE,
  `name` VARCHAR(150) NOT NULL,
  `department` VARCHAR(100) NOT NULL DEFAULT 'Computer Science and Engineering',
  `semester` INT NOT NULL DEFAULT 5,
  `credits` INT NOT NULL DEFAULT 3,
  `faculty_name` VARCHAR(150) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_subjects_sem` (`semester`, `department`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 5. ATTENDANCE RECORDS & TARGETS
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `attendance_records` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `subject_id` INT NOT NULL,
  `conducted_classes` INT NOT NULL DEFAULT 0,
  `attended_classes` INT NOT NULL DEFAULT 0,
  `target_percentage` DECIMAL(5,2) NOT NULL DEFAULT 75.00,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `uk_user_subject_attendance` (`user_id`, `subject_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`subject_id`) REFERENCES `subjects`(`id`) ON DELETE CASCADE,
  INDEX `idx_att_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 6. EXAMINATIONS
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `examinations` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `subject_id` INT NOT NULL,
  `title` VARCHAR(150) NOT NULL,
  `exam_type` ENUM('Internal Assessment 1', 'Internal Assessment 2', 'Model Exam', 'Semester End Exam', 'Lab Exam') NOT NULL DEFAULT 'Semester End Exam',
  `exam_date` DATE NOT NULL,
  `start_time` TIME NOT NULL DEFAULT '10:00:00',
  `end_time` TIME NOT NULL DEFAULT '13:00:00',
  `hall_number` VARCHAR(50) DEFAULT 'Main Block Hall 302',
  `max_marks` INT NOT NULL DEFAULT 100,
  `status` ENUM('scheduled', 'rescheduled', 'completed', 'cancelled') NOT NULL DEFAULT 'scheduled',
  `remarks` TEXT DEFAULT NULL,
  `created_by` INT DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`subject_id`) REFERENCES `subjects`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  INDEX `idx_exam_date` (`exam_date`),
  INDEX `idx_exam_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 7. ASSIGNMENTS
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `assignments` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `subject_id` INT NOT NULL,
  `title` VARCHAR(191) NOT NULL,
  `description` TEXT DEFAULT NULL,
  `deadline` DATETIME NOT NULL,
  `priority` ENUM('low', 'medium', 'high') NOT NULL DEFAULT 'medium',
  `max_score` INT NOT NULL DEFAULT 20,
  `status` ENUM('active', 'completed', 'cancelled') NOT NULL DEFAULT 'active',
  `created_by` INT DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`subject_id`) REFERENCES `subjects`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  INDEX `idx_assign_deadline` (`deadline`),
  INDEX `idx_assign_priority` (`priority`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Student Assignment Tracking
CREATE TABLE IF NOT EXISTS `student_assignment_status` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `assignment_id` INT NOT NULL,
  `status` ENUM('pending', 'in_progress', 'submitted', 'completed') NOT NULL DEFAULT 'pending',
  `submitted_at` DATETIME DEFAULT NULL,
  `student_notes` TEXT DEFAULT NULL,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `uk_user_assignment` (`user_id`, `assignment_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`assignment_id`) REFERENCES `assignments`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 8. ACADEMIC ACTIVITIES & EVENTS
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `academic_activities` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `title` VARCHAR(191) NOT NULL,
  `activity_type` ENUM('workshop', 'seminar', 'guest_lecture', 'project_review', 'symposium', 'industrial_visit', 'hackathon') NOT NULL DEFAULT 'workshop',
  `description` TEXT DEFAULT NULL,
  `activity_date` DATETIME NOT NULL,
  `venue` VARCHAR(150) NOT NULL DEFAULT 'Auditorium / Online',
  `organizer` VARCHAR(150) DEFAULT 'Department of CSE',
  `priority` ENUM('low', 'medium', 'high') NOT NULL DEFAULT 'medium',
  `status` ENUM('scheduled', 'rescheduled', 'completed', 'cancelled') NOT NULL DEFAULT 'scheduled',
  `created_by` INT DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  INDEX `idx_activity_date` (`activity_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 9. ACADEMIC DOCUMENTS, VERSIONS & CHUNKS (RAG KNOWLEDGE BASE)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `academic_documents` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `title` VARCHAR(255) NOT NULL,
  `category` ENUM('curriculum', 'exam_regulations', 'academic_calendar', 'syllabus', 'code_of_conduct', 'hostel_rules', 'scholarships') NOT NULL DEFAULT 'curriculum',
  `file_name` VARCHAR(255) NOT NULL,
  `file_path` VARCHAR(500) NOT NULL,
  `file_size_bytes` BIGINT NOT NULL DEFAULT 0,
  `mime_type` VARCHAR(100) NOT NULL DEFAULT 'application/pdf',
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `total_pages` INT NOT NULL DEFAULT 1,
  `total_chunks` INT NOT NULL DEFAULT 0,
  `language` VARCHAR(20) NOT NULL DEFAULT 'en',
  `description` TEXT DEFAULT NULL,
  `created_by` INT DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  INDEX `idx_doc_active` (`is_active`, `category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `document_versions` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `document_id` INT NOT NULL,
  `version_number` INT NOT NULL DEFAULT 1,
  `change_summary` VARCHAR(255) DEFAULT 'Initial upload',
  `file_path` VARCHAR(500) NOT NULL,
  `uploaded_by` INT DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`document_id`) REFERENCES `academic_documents`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`uploaded_by`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `document_chunks` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `document_id` INT NOT NULL,
  `chunk_index` INT NOT NULL,
  `page_number` INT NOT NULL DEFAULT 1,
  `section_title` VARCHAR(255) DEFAULT NULL,
  `content` MEDIUMTEXT NOT NULL,
  `content_length` INT NOT NULL DEFAULT 0,
  `embedding_json` JSON DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`document_id`) REFERENCES `academic_documents`(`id`) ON DELETE CASCADE,
  INDEX `idx_chunk_doc_page` (`document_id`, `page_number`),
  FULLTEXT KEY `ft_chunk_content` (`content`, `section_title`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 10. NOTIFICATIONS & DELIVERY RECORDS
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `notifications` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `message` TEXT NOT NULL,
  `notification_type` ENUM('exam', 'assignment', 'activity', 'attendance', 'study_plan', 'system') NOT NULL DEFAULT 'system',
  `priority` ENUM('low', 'medium', 'high', 'urgent') NOT NULL DEFAULT 'medium',
  `is_read` BOOLEAN NOT NULL DEFAULT FALSE,
  `read_at` DATETIME DEFAULT NULL,
  `action_link` VARCHAR(255) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  INDEX `idx_notif_user_read` (`user_id`, `is_read`),
  INDEX `idx_notif_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Deduplication & Delivery Tracking
CREATE TABLE IF NOT EXISTS `notification_delivery_records` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `dedup_key` VARCHAR(191) NOT NULL UNIQUE,
  `user_id` INT NOT NULL,
  `notification_id` INT DEFAULT NULL,
  `entity_type` VARCHAR(50) NOT NULL, -- e.g. 'exam', 'assignment'
  `entity_id` INT NOT NULL,
  `days_before` INT NOT NULL, -- e.g. 7, 3, 1, 0 (exam day)
  `delivered_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` ENUM('delivered', 'failed', 'skipped') NOT NULL DEFAULT 'delivered',
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`notification_id`) REFERENCES `notifications`(`id`) ON DELETE SET NULL,
  INDEX `idx_delivery_entity` (`entity_type`, `entity_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 11. PERSONALIZED STUDY PLANS & TASKS
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `study_plans` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `title` VARCHAR(150) NOT NULL DEFAULT 'My Weekly Academic Plan',
  `plan_type` ENUM('daily', 'weekly', 'custom') NOT NULL DEFAULT 'weekly',
  `start_date` DATE NOT NULL,
  `end_date` DATE NOT NULL,
  `target_hours_per_day` DECIMAL(3,1) NOT NULL DEFAULT 3.0,
  `completion_percentage` DECIMAL(5,2) NOT NULL DEFAULT 0.00,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  INDEX `idx_plan_user` (`user_id`, `start_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `study_tasks` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `plan_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `subject_id` INT DEFAULT NULL,
  `title` VARCHAR(191) NOT NULL,
  `description` TEXT DEFAULT NULL,
  `estimated_minutes` INT NOT NULL DEFAULT 45,
  `actual_minutes` INT NOT NULL DEFAULT 0,
  `priority` ENUM('low', 'medium', 'high') NOT NULL DEFAULT 'medium',
  `scheduled_date` DATE NOT NULL,
  `start_time` TIME DEFAULT '09:00:00',
  `is_completed` BOOLEAN NOT NULL DEFAULT FALSE,
  `completed_at` DATETIME DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`plan_id`) REFERENCES `study_plans`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`subject_id`) REFERENCES `subjects`(`id`) ON DELETE SET NULL,
  INDEX `idx_task_schedule` (`user_id`, `scheduled_date`, `is_completed`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 12. FOCUS SESSIONS (POMODORO)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `focus_sessions` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `subject_id` INT DEFAULT NULL,
  `task_id` INT DEFAULT NULL,
  `duration_minutes` INT NOT NULL DEFAULT 25,
  `break_minutes` INT NOT NULL DEFAULT 5,
  `actual_focused_seconds` INT NOT NULL DEFAULT 1500,
  `session_status` ENUM('completed', 'abandoned', 'interrupted') NOT NULL DEFAULT 'completed',
  `started_at` DATETIME NOT NULL,
  `ended_at` DATETIME NOT NULL,
  `notes` VARCHAR(255) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`subject_id`) REFERENCES `subjects`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`task_id`) REFERENCES `study_tasks`(`id`) ON DELETE SET NULL,
  INDEX `idx_focus_user` (`user_id`, `started_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 13. CHATBOT CONVERSATIONS & MESSAGES
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `chatbot_conversations` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `session_title` VARCHAR(191) NOT NULL DEFAULT 'Academic Inquiries',
  `language` ENUM('en', 'ta', 'tanglish') NOT NULL DEFAULT 'en',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  INDEX `idx_conv_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `chatbot_messages` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `conversation_id` INT NOT NULL,
  `sender` ENUM('user', 'assistant') NOT NULL,
  `message` TEXT NOT NULL,
  `detected_language` VARCHAR(20) NOT NULL DEFAULT 'en',
  `retrieved_sources` JSON DEFAULT NULL,
  `is_fallback` BOOLEAN NOT NULL DEFAULT FALSE,
  `is_supported_by_docs` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`conversation_id`) REFERENCES `chatbot_conversations`(`id`) ON DELETE CASCADE,
  INDEX `idx_msg_conv` (`conversation_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `chatbot_feedback` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `message_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `rating` ENUM('helpful', 'unhelpful') NOT NULL,
  `comments` TEXT DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`message_id`) REFERENCES `chatbot_messages`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `unanswered_questions` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `question` TEXT NOT NULL,
  `detected_language` VARCHAR(20) NOT NULL DEFAULT 'en',
  `context_attempted` TEXT DEFAULT NULL,
  `status` ENUM('pending_review', 'resolved', 'ignored') NOT NULL DEFAULT 'pending_review',
  `admin_reply` TEXT DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  INDEX `idx_unanswered_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 14. APPLICATION SETTINGS
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `application_settings` (
  `setting_key` VARCHAR(100) PRIMARY KEY,
  `setting_value` TEXT NOT NULL,
  `description` VARCHAR(255) DEFAULT NULL,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Seed default application settings
INSERT INTO `application_settings` (`setting_key`, `setting_value`, `description`) VALUES
('default_timezone', 'Asia/Kolkata', 'System default timezone for alerts and countdowns'),
('attendance_threshold', '75.0', 'Minimum required attendance percentage'),
('official_contact_academics', 'academics@college.edu | 044-2251-8000', 'Dean of Academics Office'),
('official_contact_coe', 'coe@college.edu | 044-2251-8001', 'Controller of Examinations Office'),
('system_version', '1.0.0', 'Multilingual Academic Assistant Core Version')
ON DUPLICATE KEY UPDATE `setting_value` = VALUES(`setting_value`);
