import os
import sys
import django
from datetime import datetime
from django.conf import settings
from django.test import Client
from django.urls import reverse

# Setup Django environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bhavi_fashion.settings')
django.setup()

from fpdf import FPDF
from io import StringIO
from contextlib import redirect_stdout

class TestCaseRunner:
    def __init__(self):
        self.results = []
        self.current_test = None
        
    def run_test(self, test_function, description, test_data):
        """Execute a test case and capture results"""
        self.current_test = {
            'description': description,
            'test_data': test_data,
            'status': 'Not Run',
            'actual_result': '',
            'passed': False
        }
        
        # Capture stdout during test execution
        f = StringIO()
        with redirect_stdout(f):
            try:
                test_function(test_data)
                self.current_test['status'] = 'Passed'
                self.current_test['passed'] = True
            except AssertionError as e:
                self.current_test['status'] = 'Failed'
                self.current_test['actual_result'] = str(e)
            except Exception as e:
                self.current_test['status'] = 'Error'
                self.current_test['actual_result'] = f"Unexpected error: {str(e)}"
            finally:
                self.current_test['actual_result'] += f.getvalue()
                
        self.results.append(self.current_test)
        return self.current_test['passed']

class TestReportPDF(FPDF):
    def header(self):
        logo_path = os.path.join(settings.STATIC_ROOT, 'images', 'logo.png')
        if os.path.exists(logo_path):
            self.image(logo_path, x=10, y=8, w=30)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Bhavi Fashion - Test Execution Report', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, 'Manual Verification Results', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()} | Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 0, 'C')

    def add_test_result_table(self, results):
        # Table headers
        self.set_fill_color(128, 0, 0)  # Maroon header
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 10)
        
        headers = ['TCID', 'Description', 'Test Data', 'Expected', 'Actual', 'Status']
        col_widths = [15, 45, 40, 45, 45, 20]
        
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 10, header, 1, 0, 'C', fill=True)
        self.ln()
        
        # Table data
        self.set_text_color(0, 0, 0)
        self.set_font('Arial', '', 8)
        
        for idx, result in enumerate(results, 1):
            # Check if we need a new page
            if self.get_y() > 250:
                self.add_page()
                self.set_font('Arial', 'B', 10)
                for i, header in enumerate(headers):
                    self.cell(col_widths[i], 10, header, 1, 0, 'C', fill=True)
                self.ln()
                self.set_font('Arial', '', 8)
            
            # Set color based on status
            if result['status'] == 'Passed':
                self.set_fill_color(200, 255, 200)  # Green
            elif result['status'] == 'Failed':
                self.set_fill_color(255, 200, 200)  # Red
            else:
                self.set_fill_color(255, 255, 150)  # Yellow for errors
            
            # Add row
            tcid = f"TC{idx:03d}"
            self.cell(col_widths[0], 10, tcid, 1, 0, 'C', fill=True)
            self.cell(col_widths[1], 10, result['description'], 1)
            
            # MultiCell for longer text fields
            x = self.get_x()
            y = self.get_y()
            
            # Test Data
            self.multi_cell(col_widths[2], 5, str(result['test_data']), 1, 'L')
            self.set_xy(x + col_widths[2], y)
            
            # Expected Result (from your test cases)
            expected = self.get_expected_result(idx)
            self.multi_cell(col_widths[3], 5, expected, 1, 'L')
            self.set_xy(x + col_widths[2] + col_widths[3], y)
            
            # Actual Result
            self.multi_cell(col_widths[4], 5, result['actual_result'], 1, 'L')
            self.set_xy(x + col_widths[2] + col_widths[3] + col_widths[4], y)
            
            # Status
            self.cell(col_widths[5], 10, result['status'], 1, 0, 'C')
            
            self.ln()
            self.set_fill_color(255, 255, 255)  # Reset fill color

    def get_expected_result(self, test_number):
        """Returns the expected result for each test case"""
        expected_results = {
            1: "Successful login, redirected to dashboard",
            2: "Error message: Invalid credentials",
            # Add all 41 expected results here matching your test cases
            41: "Input sanitized, no script execution"
        }
        return expected_results.get(test_number, "N/A")

def generate_test_report(output_path):
    # Initialize test runner and PDF report
    test_runner = TestCaseRunner()
    pdf = TestReportPDF()
    pdf.add_page()
    
    # Cover page
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 20, 'Bhavi Fashion Test Execution Report', 0, 1, 'C')
    pdf.ln(60)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
    pdf.cell(0, 10, 'Test Environment: Production', 0, 1, 'C')
    
    # Add test sections
    test_cases = [
        # Format: (test_function, description, test_data)
        (test_login_valid, "Valid login", {"email": "user@test.com", "password": "Test@123"}),
        (test_login_invalid, "Invalid password", {"email": "user@test.com", "password": "wrong"}),
        # Add all 41 test cases here
        (test_xss_protection, "XSS Protection", {"input": "<script>alert(1)</script>"})
    ]
    
    # Execute all tests
    for test_case in test_cases:
        test_runner.run_test(*test_case)
    
    # Generate results pages
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Test Execution Summary', 0, 1)
    pdf.ln(5)
    
    passed = sum(1 for r in test_runner.results if r['passed'])
    failed = len(test_runner.results) - passed
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'Total Tests: {len(test_runner.results)}', 0, 1)
    pdf.cell(0, 10, f'Passed: {passed}', 0, 1)
    pdf.cell(0, 10, f'Failed: {failed}', 0, 1)
    pdf.ln(10)
    
    # Detailed results
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Detailed Test Results', 0, 1)
    pdf.ln(5)
    
    pdf.add_test_result_table(test_runner.results)
    
    # Save PDF
    pdf.output(output_path)
    print(f"Test report generated at: {output_path}")

# Define your test functions here
def test_login_valid(test_data):
    """TC001: Test valid login"""
    from django.test import Client
    from django.urls import reverse
    
    client = Client()
    response = client.post(reverse('login'), {
        'email': test_data['email'],
        'password': test_data['password']
    })
    
    assert response.status_code == 302  # Redirect after login
    assert response.url == reverse('dashboard')
    print("Login successful, redirected to dashboard")

def test_login_invalid(test_data):
    """TC002: Test invalid login"""
    from django.test import Client
    from django.urls import reverse
    
    client = Client()
    response = client.post(reverse('login'), {
        'email': test_data['email'],
        'password': test_data['password']
    })
    
    assert "Invalid login credentials" in response.content.decode()
    print("Proper error message displayed")

# Define all 41 test functions following the same pattern
def test_xss_protection(test_data):
    """TC041: Test XSS protection"""
    from django.test import Client
    from django.urls import reverse
    
    client = Client()
    response = client.post(reverse('search'), {
        'query': test_data['input']
    })
    
    assert "<script>" not in response.content.decode()
    print("Input properly sanitized")

if __name__ == '__main__':
    report_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
    os.makedirs(report_dir, exist_ok=True)
    output_path = os.path.join(report_dir, 'test_execution_report.pdf')
    generate_test_report(output_path)