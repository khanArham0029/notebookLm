/*
  # Create available documents system

  1. New Tables
    - `available_documents` - Stores documents that users can select from
  
  2. Sample Data
    - Insert some sample documents for testing
  
  3. Security
    - Enable RLS on available_documents table
    - Add policies for reading available documents
*/

-- Create available_documents table for documents that users can select from
CREATE TABLE IF NOT EXISTS available_documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  type source_type NOT NULL,
  content text,
  summary text,
  url text,
  file_path text,
  file_size bigint,
  display_name text,
  metadata jsonb DEFAULT '{}',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Enable RLS
ALTER TABLE available_documents ENABLE ROW LEVEL SECURITY;

-- Allow all authenticated users to read available documents
CREATE POLICY "Users can view available documents"
  ON available_documents
  FOR SELECT
  TO authenticated
  USING (true);

-- Add trigger for updated_at
CREATE TRIGGER update_available_documents_updated_at
  BEFORE UPDATE ON available_documents
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Insert some sample documents
INSERT INTO available_documents (title, type, content, summary, display_name) VALUES
(
  'Introduction to Machine Learning',
  'pdf',
  'Machine learning is a subset of artificial intelligence that focuses on the development of algorithms and statistical models that enable computer systems to improve their performance on a specific task through experience without being explicitly programmed. This comprehensive guide covers the fundamental concepts, methodologies, and applications of machine learning in various domains.',
  'A comprehensive introduction to machine learning concepts, algorithms, and applications.',
  'ML Introduction Guide'
),
(
  'Climate Change Research Report 2024',
  'pdf',
  'This report presents the latest findings on global climate change, including temperature trends, sea level rise, and the impact of human activities on the environment. The research covers data from the past decade and provides projections for future climate scenarios based on current emission trends.',
  'Latest research findings on global climate change and environmental impact.',
  'Climate Report 2024'
),
(
  'Digital Marketing Strategies',
  'text',
  'Digital marketing has revolutionized how businesses reach and engage with their customers. This document outlines effective strategies for social media marketing, content creation, SEO optimization, and customer engagement in the digital age. It includes case studies and best practices from successful campaigns.',
  'Comprehensive guide to modern digital marketing strategies and best practices.',
  'Digital Marketing Guide'
),
(
  'Renewable Energy Technologies',
  'website',
  'Renewable energy technologies are becoming increasingly important as the world transitions away from fossil fuels. This article explores solar, wind, hydroelectric, and geothermal energy systems, their efficiency, costs, and environmental benefits. The content also discusses emerging technologies and future prospects.',
  'Overview of renewable energy technologies and their environmental benefits.',
  'Renewable Energy Overview'
),
(
  'Project Management Best Practices',
  'text',
  'Effective project management is crucial for organizational success. This document covers methodologies like Agile, Scrum, and Waterfall, along with tools and techniques for planning, execution, and monitoring. It includes templates, checklists, and real-world examples from various industries.',
  'Best practices and methodologies for effective project management.',
  'PM Best Practices'
);