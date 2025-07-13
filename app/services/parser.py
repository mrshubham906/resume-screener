import pdfplumber
import PyPDF2
import re
import logging
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from openai import OpenAI
from pydantic import BaseModel
from app.models.resume import ResumeContent, ResumeMetadata, Experience, Education
from app.config import settings

logger = logging.getLogger(__name__)


class ContactInfo(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None


class ExperienceOutput(BaseModel):
    company: str
    position: str
    duration: str
    description: str


class EducationOutput(BaseModel):
    degree: str
    institution: str
    year: Optional[str] = None


class ResumeStructuredOutput(BaseModel):
    skills: List[str]
    experience: List[ExperienceOutput]
    education: List[EducationOutput]
    contact_info: ContactInfo
    summary: str


class ResumeParser:
    """PDF Resume Parser using OpenAI for structured data extraction"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)

    def extract_text(self, pdf_path: str) -> Tuple[str, int]:
        """Extract text from PDF using multiple methods"""
        text = ""
        pages = 0
        
        try:
            # Method 1: pdfplumber (better for complex layouts)
            with pdfplumber.open(pdf_path) as pdf:
                pages = len(pdf.pages)
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # If pdfplumber didn't extract much text, try PyPDF2
            if len(text.strip()) < 100:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    pages = len(pdf_reader.pages)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            
            logger.info(f"Extracted {len(text)} characters from {pages} pages")
            return text.strip(), pages
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise

    def extract_structured_data_with_openai(self, text: str) -> Dict:
        """Use OpenAI structured output to extract structured data from resume text"""
        try:
            response = self.client.responses.parse(
                model=settings.openai_parsing_model,
                input=[
                    {
                        "role": "system",
                        "content": "You are a professional resume parser. Extract structured information from resume text and return it in the specified format."
                    },
                    {
                        "role": "user",
                        "content": f"""
                        Please analyze the following resume text and extract structured information.

                        Resume text:
                        {text[:4000]}

                        Please ensure:
                        1. Skills are technical and relevant to the job market
                        2. Experience entries include company, position, duration, and description
                        3. Education includes degree, institution, and year
                        4. Contact info includes email, phone, and LinkedIn if available
                        5. Summary is professional and concise (2-3 sentences)
                        """
                    }
                ],
                text_format=ResumeStructuredOutput
            )

            # Get the parsed output
            structured_data = response.output_parsed
            
            # Convert to dictionary format for compatibility
            result = {
                "skills": structured_data.skills,
                "experience": [
                    {
                        "company": exp.company,
                        "position": exp.position,
                        "duration": exp.duration,
                        "description": exp.description
                    }
                    for exp in structured_data.experience
                ],
                "education": [
                    {
                        "degree": edu.degree,
                        "institution": edu.institution,
                        "year": edu.year
                    }
                    for edu in structured_data.education
                ],
                "contact_info": {
                    "email": structured_data.contact_info.email,
                    "phone": structured_data.contact_info.phone,
                    "linkedin": structured_data.contact_info.linkedin
                },
                "summary": structured_data.summary
            }
            
            logger.info("Successfully extracted structured data using OpenAI structured output")
            return result
                
        except Exception as e:
            logger.error(f"OpenAI structured output API call failed: {e}")
            # Fallback to basic extraction
            return self._fallback_extraction(text)

    def _fallback_extraction(self, text: str) -> Dict:
        """Fallback extraction method if OpenAI fails"""
        logger.warning("Using fallback extraction method")
        
        # Basic email extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        email = email_match.group() if email_match else ""
        
        # Basic phone extraction
        phone_pattern = r'(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        phone_match = re.search(phone_pattern, text)
        phone = ''.join(phone_match.groups()) if phone_match else ""

        # Basic LinkedIn extraction
        linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+'
        linkedin_match = re.search(linkedin_pattern, text)
        linkedin = linkedin_match.group() if linkedin_match else ""
        
        # basic skills extraction
        skills_pattern = r'\b(?:[A-Za-z]+)\b'
        skills_match = re.findall(skills_pattern, text)
        skills = skills_match if skills_match else []


        
        return {
            "skills": skills,
            "experience": [],
            "education": [],
            "contact_info": {
                "email": email,
                "phone": phone,
                "linkedin": linkedin
            },
            "summary": text[:200] if text else "Resume content extracted"
        }

    def parse_resume(self, pdf_path: str, file_size: int) -> Tuple[ResumeContent, ResumeMetadata]:
        """Parse resume PDF and extract structured data using OpenAI"""
        start_time = datetime.now()
        
        try:
            # Extract text from PDF
            text, pages = self.extract_text(pdf_path)
            
            # Use OpenAI to extract structured data
            structured_data = self.extract_structured_data_with_openai(text)
            
            # Convert structured data to our models
            skills = structured_data.get("skills", [])
            
            # Convert experience data
            experience = []
            for exp_data in structured_data.get("experience", []):
                experience.append(Experience(
                    company=exp_data.get("company", "Unknown Company"),
                    position=exp_data.get("position", "Unknown Position"),
                    duration=exp_data.get("duration", "Unknown Duration"),
                    description=exp_data.get("description", "No description available")
                ))
            
            # Convert education data
            education = []
            for edu_data in structured_data.get("education", []):
                education.append(Education(
                    degree=edu_data.get("degree", "Unknown Degree"),
                    institution=edu_data.get("institution", "Unknown Institution"),
                    year=edu_data.get("year")
                ))
            
            # Get contact info
            contact_info = structured_data.get("contact_info", {})
            
            # Get summary
            summary = structured_data.get("summary", text[:200] if text else "Resume content extracted")
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create content object
            content = ResumeContent(
                text=text,
                skills=skills,
                experience=experience,
                education=education,
                contact_info=contact_info,
                summary=summary
            )
            
            # Create metadata object
            metadata = ResumeMetadata(
                file_size=file_size,
                pages=pages,
                processing_time=processing_time,
                extracted_at=datetime.now()
            )
            
            logger.info(f"Successfully parsed resume using OpenAI: {len(skills)} skills, {len(experience)} experiences, {len(education)} education entries")
            
            return content, metadata
            
        except Exception as e:
            logger.error(f"Failed to parse resume: {e}")
            raise 