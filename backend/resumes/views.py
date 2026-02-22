from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import fitz  # PyMuPDF
import uuid

from .supabase_utils import upload_pdf_to_supabase
from .skill_tool import SkillTool


class ResumeUploadView(APIView):
    """
    Upload PDF → Extract Text → Extract Skills (NLP + LLM)
    """

    def post(self, request):
        try:
            file = request.FILES.get("file")

            if not file:
                return Response(
                    {"error": "No file uploaded"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generate unique filename
            filename = f"{uuid.uuid4()}_{file.name}"

            # 1️⃣ Upload to Supabase
            file_url = upload_pdf_to_supabase(file, filename)

            # Reset file pointer after upload
            file.seek(0)

            # 2️⃣ Extract text using PyMuPDF
            pdf_bytes = file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            extracted_text = ""
            for page in doc:
                extracted_text += page.get_text()

            print("📄 Extracted Text Length:", len(extracted_text))

            if not extracted_text.strip():
                return Response(
                    {"error": "No text extracted from PDF"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 3️⃣ Extract skills (NLP + LLM)
            skills_data = SkillTool.run(extracted_text) 

            # 4️⃣ Return response for frontend
            return Response({
                "message": "Skills extracted successfully",
                "file_url": file_url,
                "rule_based_skills": skills_data["rule_based_skills"],
                "llm_skills": skills_data["llm_skills"],
                "all_skills": skills_data["all_skills"],
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print("❌ Upload API Error:", str(e))
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
