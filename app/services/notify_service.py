from dotenv import load_dotenv
import os
import requests

load_dotenv()

def send_teams_alert(alert_type, host_ip, criticality, message):
    """
    Sends an alert notification to Microsoft Teams webhook
    
    Args:
        alert_type (str): Type of alert (e.g., "Indisponibilidade (ICMP ping failed)")
        host_ip (str): Hostname or IP address
        criticality (str): Criticality level (e.g., "High", "Medium", "Low")
        message (str): Detailed alert message
    """
    webhook_url = os.getenv('WEBHOOK')
    if not webhook_url:
        raise ValueError("WEBHOOK environment variable not set")
    
    # Create the Teams message card
    teams_message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": get_color_for_criticality(criticality),
        "title": "🔔 EventTrace Alert",
        "summary": "New alert notification",
        "sections": [
            {
                "facts": [
                    {"name": "Tipo de alerta:", "value": alert_type},
                    {"name": "Host/IP:", "value": host_ip},
                    {"name": "Criticidade:", "value": criticality},
                    {"name": "Mensagem:", "value": message}
                ],
                "text": "Detalhes do alerta:"
            }
        ]
    }
    
    try:
        response = requests.post(webhook_url, json=teams_message)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Teams notification: {e}")
        return False

def get_color_for_criticality(criticality):
    """
    Returns theme color based on criticality level
    
    Args:
        criticality (str): Criticality level
        
    Returns:
        str: Hex color code
    """
    criticality = criticality.lower()
    if "high" in criticality:
        return "FF0000"  # Red
    elif "medium" in criticality:
        return "FFA500"  # Orange
    elif "low" in criticality:
        return "FFFF00"  # Yellow
    else:
        return "00B0F0"  # Default blue
      
# Example usage:
send_teams_alert(
    alert_type="Indisponibilidade (ICMP ping failed)",
    host_ip="192.168.1.100",
    criticality="High",
    message="Falha ao realizar ping no dispositivo por mais de 5 minutos"
)