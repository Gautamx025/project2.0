from .models import ListingCopy, VisionOutput, PriceRange, Comparable

PRODUCTS = {
    'bottle': ('Steel water bottle', 'Stainless steel', 'White', 'Drinkware', 749, 'स्टील की पानी की बोतल', 'स्टीलची पाण्याची बाटली'),
    'watch': ('Everyday digital watch', 'Mixed materials; confirm with supplier', 'White', 'Watches', 2499, 'रोज़मर्रा की डिजिटल घड़ी', 'रोजच्या वापराचे डिजिटल घड्याळ'),
    'bag': ('Everyday brown backpack', 'Leather appearance; verify material', 'Brown', 'Bags', 1899, 'रोज़मर्रा का भूरा बैकपैक', 'रोजच्या वापराची तपकिरी बॅग'),
    'custom': ('Your new shop find', 'Please confirm material', 'Please confirm color', 'General merchandise', 999, 'आपकी दुकान का नया उत्पाद', 'तुमच्या दुकानातील नवे उत्पादन'),
}

def demo_vision(key: str) -> VisionOutput:
    title, material, color, category, _, hi, mr = PRODUCTS.get(key, PRODUCTS['custom'])
    description = f'{title} for daily use. A straightforward addition to your shop catalog. Review the photo and confirm dimensions, material and specifications before selling. This is editable example copy, not a verified product assessment.'
    common = dict(tags=[category, 'Everyday', 'Shop local'], bullet_points=['A practical everyday design', 'Specifications to be confirmed by the seller', 'Carefully review before publishing'])
    english = ListingCopy(title=title, description=description, seo_title=title+' | Your local shop', seo_description=f'Shop {title.lower()}. Check the photos and ask the seller for confirmed specifications.', **common)
    hindi = ListingCopy(title=hi, tags=['स्थानीय दुकान', 'रोज़मर्रा', category], bullet_points=['रोज़मर्रा के उपयोग के लिए', 'विवरण विक्रेता से पुष्टि करें', 'प्रकाशित करने से पहले जाँचें'], description=f'{hi}। आपकी दुकान के लिए तैयार संपादन योग्य मसौदा। सामग्री, आकार और विशेषताओं की पुष्टि विक्रेता से करें। यह नमूना विवरण है।', seo_title=hi+' | आपकी दुकान', seo_description=f'{hi} खरीदें। सामग्री और आकार की सही जानकारी के लिए विक्रेता से संपर्क करें।')
    marathi = ListingCopy(title=mr, tags=['स्थानिक दुकान', 'दैनंदिन', category], bullet_points=['दैनंदिन वापरासाठी', 'तपशील विक्रेत्याकडून तपासा', 'प्रकाशित करण्यापूर्वी पडताळा'], description=f'{mr}। तुमच्या दुकानासाठी बदलता येणारा मसुदा. साहित्य, आकार आणि वैशिष्ट्ये विक्रेत्याकडून तपासा. हा नमुना मजकूर आहे.', seo_title=mr+' | तुमचे दुकान', seo_description=f'{mr} खरेदी करा. साहित्य आणि आकाराबद्दल खात्रीशीर माहितीसाठी विक्रेत्याशी संपर्क साधा.')
    return VisionOutput(**english.model_dump(), material=material, color=color, category=category, hindi=hindi, marathi=marathi)

def demo_prices(key: str) -> PriceRange:
    median = PRODUCTS.get(key, PRODUCTS['custom'])[4]
    prices = [round(median*.79), median, round(median*1.25)]
    return PriceRange(low=prices[0], median=prices[1], high=prices[2], sources=[Comparable(title=f'Illustrative comparable {i+1} — not a live offer', url='', price=price, demo=True) for i, price in enumerate(prices)])
