"""
Generate sample PDF documents for testing.
Run once: python create_sample_docs.py
"""
from fpdf import FPDF
from pathlib import Path


def create_hr_policy():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(200, 10, "HR Policy Manual", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(200, 10, "1. Leave Policy", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6,
        "Employees are eligible for 24 paid leaves annually. "
        "This includes 12 casual leaves and 12 sick leaves. "
        "Leaves must be requested at least 3 days in advance through the HR portal, "
        "except in case of emergencies. Unused leaves can be carried forward "
        "up to a maximum of 6 leaves per year. Leaves beyond the annual quota "
        "will be treated as leave without pay."
    )
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(200, 10, "2. Remote Work Policy", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6,
        "Employees may work remotely up to 3 days per week with manager approval. "
        "Remote work requests must be submitted through the HR portal. "
        "Employees working remotely must be available during core hours "
        "(10 AM - 4 PM IST) and maintain a stable internet connection. "
        "All remote workers must use company VPN for accessing internal resources."
    )
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(200, 10, "3. Performance Review", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6,
        "Performance reviews are conducted semi-annually in June and December. "
        "Each review includes self-assessment, peer feedback, and manager evaluation. "
        "Performance ratings range from 1 (Needs Improvement) to 5 (Exceptional). "
        "Employees rated 4 or above are eligible for performance bonuses. "
        "Employees rated below 2 for two consecutive cycles enter a Performance Improvement Plan (PIP)."
    )
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(200, 10, "4. Expense Reimbursement", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6,
        "Business expenses must be submitted within 30 days of occurrence. "
        "All expenses above $50 require receipts. Travel expenses are reimbursed "
        "at actuals up to the limits specified in the travel policy. "
        "Reimbursements are processed within 15 business days of submission. "
        "Late submissions beyond 30 days require VP approval."
    )

    out = Path("data/sample_documents")
    out.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out / "hr_policy.pdf"))
    print("  ✅ hr_policy.pdf")


def create_product_docs():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(200, 10, "Product Documentation - DataSync Pro", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(200, 10, "1. System Requirements", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6,
        "Minimum System Requirements:\n"
        "- Operating System: Windows 10/11, macOS 12+, Ubuntu 20.04+\n"
        "- RAM: 8 GB minimum, 16 GB recommended\n"
        "- Storage: 500 MB for installation, 10 GB for data\n"
        "- Processor: Intel i5 8th Gen or equivalent\n"
        "- Network: Stable internet connection (minimum 5 Mbps)\n"
        "- Browser: Chrome 100+, Firefox 100+, Safari 15+, Edge 100+"
    )
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(200, 10, "2. Installation Guide", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6,
        "1. Download the installer from the customer portal.\n"
        "2. Run the installer with administrator privileges.\n"
        "3. Follow the setup wizard to configure installation directory.\n"
        "4. Enter your license key when prompted.\n"
        "5. Complete the initial configuration by connecting to your database.\n"
        "6. Verify installation by accessing http://localhost:8080/health"
    )
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(200, 10, "3. API Reference", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6,
        "DataSync Pro provides RESTful APIs for integration:\n\n"
        "POST /api/v1/sync - Initiate data synchronization\n"
        "GET /api/v1/status/{job_id} - Check sync job status\n"
        "GET /api/v1/data - Retrieve synchronized data\n"
        "DELETE /api/v1/jobs/{job_id} - Cancel a sync job\n\n"
        "Authentication: Bearer token in Authorization header.\n"
        "Rate limit: 100 requests per minute per API key."
    )

    out = Path("data/sample_documents")
    out.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out / "product_docs.pdf"))
    print("  ✅ product_docs.pdf")


def create_customer_faq():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(200, 10, "Customer FAQ & Policy Guide", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(200, 10, "1. Refund Policy", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6,
        "Refunds are allowed within 30 days of purchase. "
        "To request a refund, contact support@company.com or use the "
        "self-service portal at support.company.com/refunds. "
        "Refunds are processed within 5-7 business days to the original "
        "payment method. Products that have been extensively used or "
        "customized may be subject to a 20% restocking fee. "
        "Subscription refunds are prorated based on usage."
    )
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(200, 10, "2. SLA and Support", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6,
        "Standard Support SLA: Response within 24 hours for P3 issues, "
        "4 hours for P2 issues, and 1 hour for P1 critical issues. "
        "Premium Support customers receive 2x faster response times. "
        "Support is available Monday-Friday, 9 AM - 6 PM EST. "
        "Premium customers receive 24/7 support. "
        "All support requests should be submitted through the support portal."
    )
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(200, 10, "3. Data Security", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6,
        "All customer data is encrypted at rest using AES-256 encryption. "
        "Data in transit is protected using TLS 1.3. "
        "We are SOC 2 Type II and ISO 27001 certified. "
        "Data residency options are available for EU customers (Frankfurt region). "
        "Customer data is never shared with third parties without explicit consent. "
        "Data retention period is 7 years for compliance purposes."
    )

    out = Path("data/sample_documents")
    out.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out / "customer_faq.pdf"))
    print("  ✅ customer_faq.pdf")


def create_tech_guide():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(200, 10, "Technical Guide - Deployment & Operations", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(200, 10, "1. Deployment Process", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6,
        "The deployment process follows these steps:\n"
        "1. Create a feature branch from develop.\n"
        "2. Implement changes and write unit tests (minimum 80% coverage).\n"
        "3. Submit a pull request with at least 2 reviewer approvals.\n"
        "4. CI pipeline runs: lint, test, security scan, build.\n"
        "5. Deploy to staging environment for QA validation.\n"
        "6. After QA sign-off, create release PR to main.\n"
        "7. Production deployment is automated via ArgoCD.\n"
        "8. Post-deployment health checks run automatically.\n\n"
        "Deployment windows: Tuesday-Thursday, 10 AM - 2 PM EST.\n"
        "Emergency deployments require VP Engineering approval."
    )
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(200, 10, "2. Incident Management", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6,
        "P1 (Critical): Full service outage. Response time: 15 minutes.\n"
        "P2 (High): Major feature degraded. Response time: 1 hour.\n"
        "P3 (Medium): Minor feature impact. Response time: 4 hours.\n"
        "P4 (Low): Cosmetic/minor issue. Response time: 24 hours.\n\n"
        "On-call rotation is managed through PagerDuty. "
        "All incidents must have a post-mortem within 48 hours. "
        "Blameless culture: focus on system improvements, not individual fault."
    )
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(200, 10, "3. Compliance Guidelines", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6,
        "All code must pass the following compliance checks:\n"
        "- OWASP Top 10 security scan (zero critical findings)\n"
        "- Data classification labeling on all database columns\n"
        "- PII detection scan (no unmasked PII in logs)\n"
        "- License compliance scan (no GPL dependencies in proprietary code)\n"
        "- Accessibility audit (WCAG 2.1 AA compliance for web interfaces)\n\n"
        "Quarterly compliance audits are conducted by the security team. "
        "Non-compliant services face access restrictions until remediated."
    )

    out = Path("data/sample_documents")
    out.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out / "tech_guide.pdf"))
    print("  ✅ tech_guide.pdf")


if __name__ == "__main__":
    print("Creating sample documents...")
    create_hr_policy()
    create_product_docs()
    create_customer_faq()
    create_tech_guide()
    print("\n✅ All sample documents created in data/sample_documents/")
