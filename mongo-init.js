// MongoDB initialization script for Resume Screener
// This script runs when the MongoDB container starts for the first time

// Switch to the resume_screener database
db = db.getSiblingDB('resume_screener');

// Create collections
db.createCollection('resumes');

// Create indexes for better performance
db.resumes.createIndex({ "filename": 1 });
db.resumes.createIndex({ "status": 1 });
db.resumes.createIndex({ "upload_date": -1 });
db.resumes.createIndex({ "vector_id": 1 });

// Create text index for full-text search
db.resumes.createIndex({
    "content.text": "text",
    "content.skills": "text",
    "content.summary": "text"
}, {
    weights: {
        "content.text": 10,
        "content.skills": 5,
        "content.summary": 3
    },
    name: "resume_text_search"
});

// Create compound indexes for common queries
db.resumes.createIndex({ "status": 1, "upload_date": -1 });
db.resumes.createIndex({ "status": 1, "filename": 1 });

// Insert a sample document to verify the setup
db.resumes.insertOne({
    "_id": "sample_resume_id",
    "filename": "sample_resume.pdf",
    "upload_date": new Date(),
    "status": "processed",
    "content": {
        "text": "Sample resume content for testing",
        "skills": ["Python", "FastAPI", "MongoDB"],
        "experience": [],
        "education": [],
        "contact_info": {},
        "summary": "Sample resume for testing purposes"
    },
    "metadata": {
        "file_size": 1024,
        "pages": 1,
        "processing_time": 1.0,
        "extracted_at": new Date()
    },
    "vector_id": "sample_vector_id"
});

// Remove the sample document after setup
db.resumes.deleteOne({ "_id": "sample_resume_id" });

print("MongoDB initialization completed successfully!");
print("Database: resume_screener");
print("Collection: resumes");
print("Indexes created for optimal performance"); 