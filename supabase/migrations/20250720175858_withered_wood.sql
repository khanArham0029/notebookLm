/*
  # Remove Audio Overview Fields

  1. Changes
    - Remove `audio_overview_generation_status` column from `notebooks` table
    - Remove `audio_overview_url` column from `notebooks` table  
    - Remove `audio_url_expires_at` column from `notebooks` table

  2. Security
    - No RLS changes needed as we're only removing columns
*/

-- Remove audio overview related columns from notebooks table
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'notebooks' AND column_name = 'audio_overview_generation_status'
  ) THEN
    ALTER TABLE notebooks DROP COLUMN audio_overview_generation_status;
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'notebooks' AND column_name = 'audio_overview_url'
  ) THEN
    ALTER TABLE notebooks DROP COLUMN audio_overview_url;
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'notebooks' AND column_name = 'audio_url_expires_at'
  ) THEN
    ALTER TABLE notebooks DROP COLUMN audio_url_expires_at;
  END IF;
END $$;