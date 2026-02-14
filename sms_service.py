import requests
from config import Config

class SMSService:
    def __init__(self):
        self.api_key = Config.AFRICASTALKING_API_KEY
        self.username = Config.AFRICASTALKING_USERNAME
        self.sender_id = Config.AFRICASTALKING_SENDER_ID
        self.base_url = "https://api.africastalking.com/version1/messaging"
    
    def send_sms(self, phone_number, message):
        """
        Send SMS via Africa's Talk API
        phone_number: Format +254XXXXXXXXX (Kenya)
        """
        try:
            # Ensure phone number starts with +
            if not phone_number.startswith('+'):
                if phone_number.startswith('0'):
                    phone_number = '+254' + phone_number[1:]
                elif phone_number.startswith('254'):
                    phone_number = '+' + phone_number
                else:
                    phone_number = '+254' + phone_number
            
            headers = {
                'apiKey': self.api_key,
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            data = {
                'username': self.username,
                'to': phone_number,
                'message': message,
                'from': self.sender_id
            }
            
            response = requests.post(self.base_url, headers=headers, data=data)
            
            if response.status_code == 201:
                result = response.json()
                return {'success': True, 'data': result}
            else:
                return {'success': False, 'error': f'API Error: {response.status_code}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_exam_reminder(self, phone_number, student_name, exam_name, exam_time):
        """Send exam reminder SMS"""
        message = f"Hello {student_name}, your exam '{exam_name}' is scheduled for {exam_time}. Login at http://ouk-exams.com to take your exam. - Open University of Kenya"
        return self.send_sms(phone_number, message)
    
    def send_exam_started(self, phone_number, student_name, exam_name):
        """Notify when exam starts"""
        message = f"Hello {student_name}, your exam '{exam_name}' has started. Good luck! - OUK"
        return self.send_sms(phone_number, message)
    
    def send_exam_completed(self, phone_number, student_name, exam_name):
        """Notify when exam is submitted"""
        message = f"Hello {student_name}, your exam '{exam_name}' has been submitted successfully. Results will be available soon. - OUK"
        return self.send_sms(phone_number, message)
    
    def send_bulk_sms(self, phone_numbers, message):
        """Send SMS to multiple recipients"""
        results = []
        for phone in phone_numbers:
            result = self.send_sms(phone, message)
            results.append({'phone': phone, 'result': result})
        return results
