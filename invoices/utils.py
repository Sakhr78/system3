from num2words import num2words

def convert_number_to_words(number):
    """تحويل الأرقام إلى نصوص عربية مع إضافة كلمة 'ريال' في النهاية"""
    if number is None:
        return "صفر ريال"
    
    # تحويل الرقم إلى نص
    words = num2words(number, lang='ar')

    # إضافة كلمة ريال في النهاية
    return f"{words} ريال"
