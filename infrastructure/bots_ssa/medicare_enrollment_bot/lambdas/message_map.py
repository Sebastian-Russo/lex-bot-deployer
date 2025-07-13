"""
Message mapping for Medicare Enrollment Bot.
Maps prompt IDs to actual message content.
"""


class MessageMap:
    """Message mapping for Medicare Enrollment Bot"""

    # English messages
    ENGLISH = {
        # Main flow prompts
        'P1370English': 'Ok, Medicare. One moment. Are you enrolled in Medicare?',
        'P1370aEnglish': "Let's try again. Medicare. Are you enrolled in Medicare?",
        'P1372English': 'Do you want a new medicare card?',
        'P1372aEnglish': "Let's try again. Do you want a replacement medicare card?",
        'P1373English': 'Are you calling to get help covering the cost of medications?',
        'P1373aEnglish': "Let's try again. Are you calling to get help covering the cost of medications?",
        'P1374English': 'Are you already enrolled in the program to help cover the cost of medications called Part D?',
        'P1374aEnglish': "Let's try again. Are you already enrolled in the program to help cover the cost of medications called Part D?",
        'P1375English': 'Some people may have the right to receive help covering their medication expenses. To receive additional help, your resources must be less than {individual_maximum} for an individual, or {couple_maximum} for a married couple living together. Examples of resources include savings, investments, and real estate. We do not include the house you live in, vehicles, burial plots, or personal property. However, there are income limits that will be taken into account if you decide to apply for this help. The law changes will allow some people to have the right to receive additional help. The Social Security Administration will not consider the help you receive for home expenses or life insurance policies when determining your eligibility. You can also receive help with Medicare expenses in your state through the Medicare Savings Program. Applications for this help can begin the process of applying for Medicare Savings Programs in your state. We will send your information to your state and they will contact you to help you apply for Medicare Savings Programs, unless you tell us not to.',
        'P1376English': 'Do you want to hear the information again?',
        'P1376aEnglish': "Let's try again. Do you want to hear the information about the help covering your medication expenses?",
        'P1377English': 'Do you want to receive an application for help covering your medication expenses?',
        'P1377aEnglish': "Let's try again. Do you want to receive an application for help covering your medication expenses?",
        'P1382English': 'If you are finished, you can disconnect. If not, please wait and I will return you to the main menu.',
        # Block A prompts
        'P1378English': 'You can get more information about the help covering your medication expenses (known as Part D) or the Medicare state programs that can help you with your health care expenses, by calling 1-800-633-4227. That number is, 1-800-633-4227. This information is also available on your website, at www dot Medicare dot G O V.',
        'P1379English': 'Do you want to hear the information again?',
        'P1379aEnglish': "Let's try again. Do you want to hear the information about applying for Part D of Medicare again?",
        # Block B prompts
        'P1380English': 'To enroll in the regular Medicare program for help covering medication expenses, called Part D, you must be enrolled, or eligible for Part A of Medicare, hospital coverage, or Part B, which offers medical services, medical vision coverage, and other services not covered by Part A. Once you are enrolled in Part A or Part B, you can enroll yourself in the program for help covering medication expenses, called Part D, through an authorized provider of the program for help covering medication expenses of Medicare, or through a Medicare coverage plan for medication expenses that offers coverage for medication expenses. To get more information, call 1-800-633-4227. Repeating the number is, 1-800-633-4227, or visit the website, Medicare dot G O V.',
        'P1381English': 'Do you want to hear the information again?',
        'P1381aEnglish': "Let's try again. Do you want to hear the information about enrolling in the regular Medicare program for help covering medication expenses?",
        # Transfer messages
        'TRANSFER_MEDICARE_CARD': 'Transferring to Medicare Replacement Card bot.',
        'TRANSFER_EXTRA_HELP': 'Transferring to Medicare Prescription Drug Extra Help.',
        # Error messages
        'ERROR_PROCESSING': "I'm sorry, there was an error processing your request.",
        'INVALID_RESPONSE': "I didn't understand your response. Please say yes or no.",
    }

    # Spanish messages - to be added later
    SPANISH = {
        # Main flow prompts
        'P1370Spanish': 'Ok, Medicare. Un momento. ¿Está inscrito en Medicare?',
        'P1370aSpanish': 'Intentemos de nuevo. Medicare. ¿Está inscrito en Medicare?',
        'P1372Spanish': '¿Desea una nueva tarjeta de Medicare?',
        'P1372aSpanish': 'Intentemos de nuevo. ¿Desea una tarjeta de reemplazo de Medicare?',
        'P1373Spanish': '¿Está llamando para obtener ayuda para cubrir el costo de los medicamentos?',
        'P1373aSpanish': 'Intentemos de nuevo. ¿Está llamando para obtener ayuda para cubrir el costo de los medicamentos?',
        'P1374Spanish': '¿Ya está inscrito en el programa para ayudar a cubrir el costo de los medicamentos llamado Parte D?',
        'P1374aSpanish': 'Intentemos de nuevo. ¿Ya está inscrito en el programa para ayudar a cubrir el costo de los medicamentos llamado Parte D?',
        'P1375Spanish': 'Algunas personas pueden tener derecho a recibir ayuda para cubrir sus gastos de medicamentos. Para recibir ayuda adicional, sus recursos deben ser inferiores a {individual_maximum} para un individuo, o {couple_maximum} para una pareja casada que vive junta. Ejemplos de recursos incluyen ahorros, inversiones y bienes raíces. No incluimos la casa en la que vive, vehículos, parcelas de entierro o propiedad personal. Sin embargo, hay límites de ingresos que se tendrán en cuenta si decide solicitar esta ayuda. Los cambios en la ley permitirán que algunas personas tengan derecho a recibir ayuda adicional. La Administración del Seguro Social no considerará la ayuda que recibe para gastos del hogar o pólizas de seguro de vida al determinar su elegibilidad. También puede recibir ayuda con los gastos de Medicare en su estado a través del Programa de Ahorros de Medicare. Las solicitudes para esta ayuda pueden iniciar el proceso de solicitud de Programas de Ahorros de Medicare en su estado. Enviaremos su información a su estado y ellos se comunicarán con usted para ayudarlo a solicitar los Programas de Ahorros de Medicare, a menos que nos indique que no lo hagamos.',
        'P1376Spanish': '¿Quiere escuchar la información de nuevo?',
        'P1376aSpanish': 'Intentemos de nuevo. ¿Quiere escuchar la información sobre la ayuda para cubrir sus gastos de medicamentos?',
        'P1377Spanish': '¿Desea recibir una solicitud para ayuda para cubrir sus gastos de medicamentos?',
        'P1377aSpanish': 'Intentemos de nuevo. ¿Desea recibir una solicitud para ayuda para cubrir sus gastos de medicamentos?',
        'P1382Spanish': 'Si ha terminado, puede desconectarse. Si no, espere y lo devolveré al menú principal.',
        # Block A prompts
        'P1378Spanish': 'Puede obtener más información sobre la ayuda para cubrir sus gastos de medicamentos (conocida como Parte D) o los programas estatales de Medicare que pueden ayudarlo con sus gastos de atención médica, llamando al 1-800-633-4227. Ese número es, 1-800-633-4227. Esta información también está disponible en su sitio web, en www punto Medicare punto G O V.',
        'P1379Spanish': '¿Quiere escuchar la información de nuevo?',
        'P1379aSpanish': 'Intentemos de nuevo. ¿Quiere escuchar la información sobre cómo solicitar la Parte D de Medicare de nuevo?',
        # Block B prompts
        'P1380Spanish': 'Para inscribirse en el programa regular de Medicare para ayudar a cubrir los gastos de medicamentos, llamado Parte D, debe estar inscrito o ser elegible para la Parte A de Medicare, cobertura hospitalaria, o la Parte B, que ofrece servicios médicos, cobertura de visión médica y otros servicios no cubiertos por la Parte A. Una vez que esté inscrito en la Parte A o B, puede inscribirse en el programa para ayudar a cubrir los gastos de medicamentos, llamado Parte D, a través de un proveedor autorizado del programa para ayudar a cubrir los gastos de medicamentos de Medicare, o a través de un plan de cobertura de Medicare para gastos de medicamentos que ofrece cobertura para gastos de medicamentos. Para obtener más información, llame al 1-800-633-4227. Repitiendo el número es, 1-800-633-4227, o visite el sitio web, Medicare punto G O V.',
        'P1381Spanish': '¿Quiere escuchar la información de nuevo?',
        'P1381aSpanish': 'Intentemos de nuevo. ¿Quiere escuchar la información sobre cómo inscribirse en el programa regular de Medicare para ayudar a cubrir los gastos de medicamentos?',
        # Transfer messages
        'TRANSFER_MEDICARE_CARD': 'Transfiriendo al bot de Reemplazo de Tarjeta de Medicare.',
        'TRANSFER_EXTRA_HELP': 'Transfiriendo a Ayuda Extra para Medicamentos Recetados de Medicare.',
        # Error messages
        'ERROR_PROCESSING': 'Lo siento, hubo un error al procesar su solicitud.',
        'INVALID_RESPONSE': 'No entendí su respuesta. Por favor diga sí o no.',
    }

    @staticmethod
    def get_message(message_id, language='en_US', **kwargs):
        """
        Get message by ID and language

        Args:
            message_id (str): The message ID (e.g., "P1370English")
            language (str): The language ("English" or "Spanish")
            **kwargs: Variables to format into the message

        Returns:
            str: The formatted message
        """
        message_map = MessageMap.ENGLISH if language == 'en_US' else MessageMap.SPANISH

        # Handle combined message IDs (e.g., "P1375English + P1376English")
        if ' + ' in message_id:
            # Always combine individual messages when a combined ID is provided
            # We don't store pre-combined messages anymore
            parts = message_id.split(' + ')
            messages = []
            for part in parts:
                part_message = message_map.get(part)
                if part_message:
                    messages.append(part_message)
            message = ' '.join(messages) if messages else None
        else:
            message = message_map.get(message_id)

        # Format message with variables if provided
        if message and kwargs:
            try:
                message = message.format(**kwargs)
            except KeyError as e:
                # Log error but return unformatted message
                print(f'Error formatting message {message_id}: Missing key {e}')

        return message or f'Message not found: {message_id}'
