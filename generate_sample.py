# Simple script to generate a sample PYQ PDF to test the app immediately
from pypdf import PdfWriter
import io

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    def create_sample_pyq_pdf(output_path="sample_exam_pyq.pdf"):
        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter

        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "NATIONAL COMPETITIVE EXAM - PREVIOUS YEAR QUESTIONS (2025)")
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 70, "Time Allowed: 3 Hours | Total Questions: 6 | Subject: Mixed Science & CS")
        c.line(50, height - 80, width - 50, height - 80)

        y = height - 110

        # Section 1
        c.setFont("Helvetica-Bold", 13)
        c.drawString(50, y, "SECTION A: PHYSICS")
        y -= 25

        c.setFont("Helvetica", 11)
        c.drawString(50, y, "1. What is the SI unit of electric potential?")
        y -= 18
        c.drawString(70, y, "(A) Ampere")
        y -= 16
        c.drawString(70, y, "(B) Volt")
        y -= 16
        c.drawString(70, y, "(C) Ohm")
        y -= 16
        c.drawString(70, y, "(D) Joule")
        y -= 18
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(70, y, "Ans: (B) Explanation: Electric potential is measured in Volts (Joules per Coulomb).")
        y -= 30

        c.setFont("Helvetica", 11)
        c.drawString(50, y, "2. A body of mass 5 kg moves with an acceleration of 2 m/s^2. What is the net force?")
        y -= 18
        c.drawString(70, y, "(A) 2.5 N")
        y -= 16
        c.drawString(70, y, "(B) 10 N")
        y -= 16
        c.drawString(70, y, "(C) 7 N")
        y -= 16
        c.drawString(70, y, "(D) 20 N")
        y -= 18
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(70, y, "Ans: (B) Explanation: F = m * a = 5 * 2 = 10 N.")
        y -= 40

        # Section 2
        c.setFont("Helvetica-Bold", 13)
        c.drawString(50, y, "SECTION B: COMPUTER SCIENCE")
        y -= 25

        c.setFont("Helvetica", 11)
        c.drawString(50, y, "3. Which data structure follows the LIFO (Last In First Out) principle?")
        y -= 18
        c.drawString(70, y, "(A) Queue")
        y -= 16
        c.drawString(70, y, "(B) Stack")
        y -= 16
        c.drawString(70, y, "(C) Binary Tree")
        y -= 16
        c.drawString(70, y, "(D) Array")
        y -= 18
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(70, y, "Ans: (B) Explanation: Stacks use LIFO ordering (push and pop at top).")
        y -= 30

        c.setFont("Helvetica", 11)
        c.drawString(50, y, "4. What is the time complexity of searching an element in a balanced Binary Search Tree?")
        y -= 18
        c.drawString(70, y, "(A) O(1)")
        y -= 16
        c.drawString(70, y, "(B) O(N)")
        y -= 16
        c.drawString(70, y, "(C) O(log N)")
        y -= 16
        c.drawString(70, y, "(D) O(N log N)")
        y -= 18
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(70, y, "Ans: (C) Explanation: Height of balanced BST is log(N).")
        y -= 40

        c.showPage()
        c.save()
        print(f"Sample PDF created at {output_path}")

    if __name__ == "__main__":
        create_sample_pyq_pdf()
except ImportError:
    pass
