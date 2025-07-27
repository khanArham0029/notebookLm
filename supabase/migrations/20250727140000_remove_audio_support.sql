-- Remove audio-related configurations

-- Remove 'audio' from source_type ENUM
ALTER TYPE source_type RENAME VALUE 'audio' TO 'audio_old';
ALTER TYPE source_type ADD VALUE 'audio_temp';
ALTER TABLE public.sources ALTER COLUMN type TYPE source_type USING type::text::source_type;
ALTER TYPE source_type RENAME VALUE 'audio_temp' TO 'audio';

-- IMPORTANT: Update existing rows that might still use 'audio_old'
-- This ensures no columns reference the value before it's dropped.
UPDATE public.sources
SET type = 'text'
WHERE type::text = 'audio_old';

ALTER TYPE source_type DROP VALUE 'audio_old';

-- This is a workaround to remove an enum value in PostgreSQL.
-- A more robust solution for production might involve creating a new enum type
-- and migrating data, but for simple removal, this is often sufficient.

-- Delete the 'audio' storage bucket
DELETE FROM storage.buckets WHERE id = 'audio';

-- Remove audio MIME types from the 'sources' storage bucket
UPDATE storage.buckets
SET allowed_mime_types = array_remove(allowed_mime_types, 'audio/mpeg')
WHERE id = 'sources';

UPDATE storage.buckets
SET allowed_mime_types = array_remove(allowed_mime_types, 'audio/wav')
WHERE id = 'sources';

UPDATE storage.buckets
SET allowed_mime_types = array_remove(allowed_mime_types, 'audio/mp4')
WHERE id = 'sources';

UPDATE storage.buckets
SET allowed_mime_types = array_remove(allowed_mime_types, 'audio/m4a')
WHERE id = 'sources';

-- Drop RLS policies for the 'audio' bucket (if they still exist after bucket deletion)
DROP POLICY IF EXISTS "Users can view their own audio files" ON storage.objects;
DROP POLICY IF EXISTS "Service role can manage audio files" ON storage.objects;
DROP POLICY IF EXISTS "Users can delete their own audio files" ON storage.objects;