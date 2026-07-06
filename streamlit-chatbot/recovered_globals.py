# Recovered global variables from compiled bytecode

LOCAL_GREETINGS = {'greetings': 'Greetings! I am your local fallback assistant. The remote AI service is currently offline. How can I '
              'assist you today?',
 'hello': 'Hello! I am your local fallback assistant. The remote AI service is currently unavailable, but I am here to '
          'help you locally. What can I do for you today?',
 'hey': 'Hi there! I am your local fallback assistant. The remote AI service is currently unavailable, but I am here '
        'to help you locally. What can I do for you today?',
 'hi': 'Hello! I am your local fallback assistant. The remote AI service is currently unavailable, but I am here to '
       'help you locally. What can I do for you today?',
 'how are you': 'I am doing well, thank you! As a local fallback assistant, I am running completely on your system '
                'because the remote AI service is offline. How can I help you?'}


LOCAL_KNOWLEDGE_BASE = {'ai': 'Artificial Intelligence (AI) refers to the simulation of human intelligence processes by machines, especially '
       'computer systems. These processes include learning (the acquisition of information and rules for using it), '
       'reasoning (using rules to reach conclusions), and self-correction.',
 'artificial intelligence': 'Artificial Intelligence (AI) refers to the simulation of human intelligence processes by '
                            'machines, especially computer systems. These processes include learning, reasoning, and '
                            'self-correction.',
 'asthma': 'Asthma is a chronic respiratory condition characterized by inflammation and narrowing of the airways, '
           'which causes difficulty breathing, wheezing, shortness of breath, and coughing. It is commonly triggered '
           'by allergens, exercise, or cold air.',
 'machine learning': 'Machine Learning (ML) is a subset of artificial intelligence that enables computers to learn '
                     'from data and improve their performance over time without being explicitly programmed.',
 'medquad': 'MedQuAD is a medical Q&A dataset containing pairs of questions and answers from NIH (National Institutes '
            'of Health) services, covering various diseases, symptoms, treatments, and drugs.',
 'python': 'Python is a high-level, interpreted programming language known for its readability, simplicity, and '
           'versatility. It is widely used in web development, data science, artificial intelligence, machine '
           'learning, automation, and software prototyping.'}


LOCAL_GREETINGS_EN = ['Hello! I am your local fallback assistant. The remote AI service is currently unavailable, but I am here to help you '
 'locally.',
 'Hi there! As your local fallback assistant, I am running completely on your system because the remote AI service is '
 'offline.',
 'Hey! I am your local fallback assistant. Although the main Gemini service is currently offline, I can still answer '
 'basic questions and check the time for you.',
 'Greetings! Since the remote Gemini server is currently unreachable and offline, I am assisting as your local '
 'fallback assistant. What can I do for you today?']


LOCAL_GREETINGS_HI = ['नमस्ते! मैं आपका स्थानीय फ़ॉलबैक सहायक (local fallback assistant) हूँ। रिमोट एआई सेवा वर्तमान में अनुपलब्ध '
 '(unavailable) है, लेकिन मैं आपकी सहायता के लिए यहाँ हूँ।',
 'हैलो! आपके स्थानीय फ़ॉलबैक सहायक (local fallback assistant) के रूप में, मैं पूरी तरह से आपके सिस्टम पर काम कर रहा '
 'हूँ क्योंकि रिमोट एआई सेवा ऑफ़लाइन (offline) है।',
 'नमस्कार! हालांकि मुख्य जेमिनी सेवा वर्तमान में ऑफ़लाइन (offline) है, फिर भी मैं एक स्थानीय फ़ॉलबैक सहायक (local '
 'fallback assistant) के रूप में बुनियादी सवालों के जवाब दे सकता हूँ।',
 'प्रणाम! चूंकि रिमोट जेमिनी सर्वर वर्तमान में पहुंच से बाहर और ऑफ़लाइन (offline) है, मैं स्थानीय फ़ॉलबैक सहायक (local '
 'fallback assistant) के रूप में आपकी सहायता कर रहा हूँ।']


LOCAL_DEFAULT_HELP_EN = ['I am here as your local fallback assistant to ensure you get a response even without internet connectivity.\n'
 '\n'
 'You can:\n'
 '- Ask for the current **time** or **date**.\n'
 '- Ask basic questions about **Python**, **AI**, or **Asthma**.\n'
 '- Upload a document in the **📂 Knowledge Base** sidebar section to search it locally.',
 'As an offline local fallback assistant, my knowledge is limited to built-in topics, but I will do my best to assist '
 'you.\n'
 '\n'
 'Try asking about:\n'
 '- **Python** programming basics (loops, functions, variables).\n'
 '- **Asthma** medical information.\n'
 '- **AI** and tech concepts (machine learning, cloud computing).\n'
 '- Current **date and time**.',
 'The remote AI API is not reachable, so I am operating as a local fallback assistant in offline mode.\n'
 '\n'
 'Here are some things I can do:\n'
 '1. Answer programming questions about functions, loops, and variables.\n'
 '2. Explain general tech and AI topics.\n'
 '3. Show the current system date/time.\n'
 "4. Search your uploaded documents if you're in Knowledge Base mode."]


LOCAL_DEFAULT_HELP_HI = ['मैं यहाँ आपके स्थानीय फ़ॉलबैक सहायक (local fallback assistant) के रूप में हूँ ताकि यह सुनिश्चित किया जा सके कि आपको '
 'इंटरनेट कनेक्टिविटी के बिना भी प्रतिक्रिया मिले।\n'
 '\n'
 'आप:\n'
 '- वर्तमान **समय** या **तारीख** पूछ सकते हैं।\n'
 '- **पायथन**, **एआई**, या **अस्थमा** के बारे में बुनियादी सवाल पूछ सकते हैं।\n'
 '- इसे स्थानीय रूप से खोजने के लिए साइडबार के **📂 ज्ञानकोश** अनुभाग में एक दस्तावेज़ अपलोड कर सकते हैं।',
 'एक ऑफ़लाइन स्थानीय फ़ॉलबैक सहायक (local fallback assistant) के रूप में, मेरा ज्ञान सीमित है, लेकिन मैं आपकी सहायता '
 'करने की पूरी कोशिश करूँगा।\n'
 '\n'
 'आप पूछ सकते हैं:\n'
 '- **पायथन** प्रोग्रामिंग की बुनियादी बातें (लूप, फंक्शन, वेरिएबल)।\n'
 '- **अस्थमा** से संबंधित चिकित्सा जानकारी।\n'
 '- **एआई** और तकनीक अवधारणाएं (मशीन लर्निंग, क्लाउड कंप्यूटिंग)।\n'
 '- वर्तमान **तारीख और समय**।',
 'रिमोट जेमिनी एपीआई उपलब्ध नहीं है, इसलिए मैं एक स्थानीय फ़ॉलबैक सहायक (local fallback assistant) के रूप में ऑफ़लाइन '
 'मोड में काम कर रहा हूँ।\n'
 '\n'
 'यहाँ कुछ चीज़ें दी गई हैं जो मैं कर सकता हूँ:\n'
 '1. फंक्शन, लूप और वेरिएबल के बारे में प्रोग्रामिंग प्रश्नों के उत्तर देना।\n'
 '2. सामान्य तकनीक और एआई विषयों को समझाना।\n'
 '3. वर्तमान सिस्टम तिथि/समय दिखाना।\n'
 '4. दस्तावेज़ों को स्थानीय रूप से खोजना यदि आप ज्ञानकोश मोड में हैं।']


OFFLINE_TOPICS = {'ai': {'en': ['Artificial Intelligence refers to the simulation of human cognitive processes by computer systems.',
               'Machine Learning, a core subset of AI, enables algorithms to learn patterns directly from data without '
               'explicit programming.',
               'Deep learning uses neural networks with many layers to model complex representations, powering modern '
               'computer vision and NLP.',
               'Today, AI technology is transforming industries by automating tasks, providing insights, and driving '
               'intelligent applications.'],
        'hi': ['कृत्रिम बुद्धिमत्ता (एआई) कंप्यूटर सिस्टम द्वारा मानव संज्ञानात्मक प्रक्रियाओं के अनुकरण को संदर्भित '
               'करती है।',
               'मशीन लर्निंग एआई का एक मुख्य उपसमुच्चय है जो एल्गोरिदम को बिना स्पष्ट प्रोग्रामिंग के डेटा से पैटर्न '
               'सीखने की अनुमति देता है।',
               'डीप लर्निंग जटिल अभ्यावेदन को मॉडल करने के लिए कई परतों वाले न्यूरल नेटवर्क का उपयोग करता है, जो '
               'आधुनिक विज़न और एनएलपी को शक्ति प्रदान करता है।',
               'आज, एआई तकनीक कार्यों को स्वचालित करके, अंतर्दृष्टि प्रदान करके और बुद्धिमान अनुप्रयोगों को चलाकर '
               'उद्योगों को बदल रही है।'],
        'subtopics': {'work': {'en': ['AI systems work by combining large datasets with intelligent, iterative '
                                      'processing algorithms, allowing the software to learn automatically from '
                                      'patterns in the data.'],
                               'hi': ['एआई सिस्टम बड़ी मात्रा में डेटा को बुद्धिमान, पुनरावृत्तीय प्रसंस्करण एल्गोरिदम '
                                      'के साथ जोड़कर काम करते हैं, जिससे सॉफ्टवेयर डेटा में पैटर्न से स्वचालित रूप से '
                                      'सीखता है।']}}},
 'asthma': {'en': ['Asthma is a chronic inflammatory disease that affects the airways of the lungs, causing temporary '
                   'breathing difficulties.',
                   'Common symptoms include episodes of wheezing, coughing, chest tightness, and shortness of breath.',
                   'These episodes are typically triggered by exposure to allergens, environmental pollutants, cold '
                   'air, or physical exertion.',
                   'While there is no cure, asthma symptoms can be effectively managed with inhalers and avoiding '
                   'known triggers.'],
            'hi': ['अस्थमा फेफड़ों के वायुमार्ग को प्रभावित करने वाली एक पुरानी सूजन संबंधी बीमारी है, जिससे सांस लेने '
                   'में कठिनाई होती है।',
                   'सामान्य लक्षणों में घरघराहट, खांसी, छाती में जकड़न और सांस फूलना शामिल हैं।',
                   'ये दौरे आमतौर पर एलर्जी, पर्यावरणीय प्रदूषक, ठंडी हवा या शारीरिक श्रम के संपर्क में आने से शुरू '
                   'होते हैं।',
                   'हालांकि इसका कोई स्थायी इलाज नहीं है, लेकिन इनहेलर और ट्रिगर्स से बचकर अस्थमा के लक्षणों को '
                   'प्रभावी ढंग से प्रबंधित किया जा सकता है।'],
            'subtopics': {'cause': {'en': ['Asthma causes and triggers include airborne substances like pollen, dust '
                                           'mites, mold spores, pet dander, respiratory infections, physical activity, '
                                           'and cold air.'],
                                    'hi': ['अस्थमा के कारणों और ट्रिगर्स में हवा के कण जैसे पराग, धूल के कण, पालतू '
                                           'जानवरों की रूसी, श्वसन संक्रमण, शारीरिक गतिविधि और ठंडी हवा शामिल हैं।']},
                          'symptom': {'en': ['Major symptoms of asthma are shortness of breath, wheezing (a whistling '
                                             'sound when breathing out), coughing (especially at night), and chest '
                                             'tightness.'],
                                      'hi': ['अस्थमा के प्रमुख लक्षण हैं सांस की तकलीफ, घरघराहट (सांस छोड़ते समय सीटी '
                                             'जैसी आवाज), खांसी (विशेषकर रात में), और छाती में जकड़न।']},
                          'treat': {'en': ['Treatment usually involves long-term asthma control medications (like '
                                           'inhaled corticosteroids) and quick-relief inhalers (like albuterol) for '
                                           'acute flare-ups.'],
                                    'hi': ['उपचार में आमतौर पर दीर्घकालिक नियंत्रण दवाएं (जैसे इनहेल्ड '
                                           'कॉर्टिकोस्टेरॉइड्स) और तीव्र हमलों के लिए त्वरित-राहत इनहेलर शामिल होते '
                                           'हैं।']}}},
 'delhi': {'en': ['New Delhi is the capital city of India, serving as the seat of all three branches of the Government '
                  'of India.',
                  'It is a historical and cultural hub, featuring prominent landmarks like the India Gate, Red Fort, '
                  'and Rashtrapati Bhavan.',
                  "It hosts the Parliament of India and is the center of the nation's political life."],
           'hi': ['नई दिल्ली भारत की राजधानी है, जो भारत सरकार की तीनों शाखाओं के मुख्यालय के रूप में कार्य करती है।',
                  'यह एक ऐतिहासिक और सांस्कृतिक केंद्र है, जिसमें इंडिया गेट, लाल किला और राष्ट्रपति भवन जैसे प्रमुख '
                  'स्थल शामिल हैं।',
                  'यह भारतीय संसद की मेजबानी करता है और देश के राजनीतिक जीवन का केंद्र है।']},
 'earth': {'en': ['Earth is the third planet from the Sun and the only astronomical object known to harbor life.',
                  'It has a liquid water ocean covering about 71% of its surface, and an atmosphere rich in nitrogen '
                  'and oxygen.',
                  'Its active plate tectonics and magnetic field protect life from harmful solar radiation, making it '
                  'a unique sanctuary.'],
           'hi': ['पृथ्वी सूर्य से तीसरा ग्रह है और जीवन को आश्रय देने वाला एकमात्र ज्ञात खगोलीय पिंड है।',
                  'इसकी सतह का लगभग 71% हिस्सा तरल पानी से ढका है, और इसका वायुमंडल नाइट्रोजन और ऑक्सीजन से समृद्ध है।',
                  'इसकी सक्रिय प्लेट टेक्टोनिक्स और चुंबकीय क्षेत्र जीवन को हानिकारक सौर विकिरण से बचाते हैं।']},
 'functions': {'en': ['A function is a reusable block of organized, self-contained code designed to perform a single, '
                      'related action.',
                      'Functions help break programs into smaller modular parts, making the codebase easier to test, '
                      'debug, and maintain.',
                      'They can accept input parameters and return output values, acting as the building blocks of '
                      'modern software.'],
               'hi': ['फंक्शन संगठित, स्व-निहित कोड का एक पुन: प्रयोज्य ब्लॉक है जिसे एक एकल, संबंधित कार्य करने के '
                      'लिए डिज़ाइन किया गया है।',
                      'फंक्शन प्रोग्राम को छोटे मॉड्यूलर भागों में विभाजित करने में मदद करते हैं, जिससे कोडबेस का '
                      'परीक्षण और रखरखाव आसान हो जाता है।',
                      'वे इनपुट पैरामीटर स्वीकार कर सकते हैं और आउटपुट मान वापस कर सकते हैं, जो आधुनिक सॉफ्टवेयर के '
                      'निर्माण ब्लॉक के रूप में कार्य करते हैं।']},
 'gravity': {'en': ['Gravity is a fundamental interaction that causes mutual attraction between all things with mass '
                    'or energy.',
                    'On Earth, gravity gives weight to physical objects and holds the atmosphere and oceans in place.',
                    "It is described by Albert Einstein's general theory of relativity as a consequence of the "
                    'curvature of spacetime.'],
             'hi': ['गुरुत्वाकर्षण एक मौलिक अंतःक्रिया है जो द्रव्यमान या ऊर्जा वाली सभी चीजों के बीच आपसी आकर्षण का '
                    'कारण बनती है।',
                    'पृथ्वी पर, गुरुत्वाकर्षण भौतिक वस्तुओं को भार देता है और वायुमंडल और महासागरों को स्थिर रखता है।',
                    'अल्बर्ट आइंस्टीन के सामान्य सापेक्षता के सिद्धांत में इसे स्पेसटाइम की वक्रता के परिणाम के रूप '
                    'में वर्णित किया गया है।']},
 'india': {'en': ['India is a country in South Asia, known for its rich history, diverse culture, and democratic '
                  'foundation.',
                  'It is the seventh-largest country by area and the most populous nation in the world.',
                  'India achieved independence from British rule in 1947 and has since grown into a major global '
                  'economic power.'],
           'hi': ['भारत दक्षिण एशिया का एक देश है, जो अपने समृद्ध इतिहास, विविध संस्कृति और लोकतांत्रिक नींव के लिए '
                  'जाना जाता है।',
                  'यह क्षेत्रफल के हिसाब से सातवां सबसे बड़ा देश और दुनिया का सबसे अधिक आबादी वाला देश है।',
                  'भारत ने 1947 में ब्रिटिश शासन से स्वतंत्रता प्राप्त की और तब से एक प्रमुख वैश्विक आर्थिक शक्ति के '
                  'रूप में विकसित हुआ है।']},
 'loops': {'en': ['A loop is a fundamental programming control flow structure that repeats a block of code while a '
                  'specified condition remains true.',
                  "Common types of loops include 'for' loops, which iterate over a sequence, and 'while' loops, which "
                  'run as long as a condition holds.',
                  'Using loops helps eliminate duplicate code and allows programs to process lists or streams of data '
                  'efficiently.'],
           'hi': ['लूप एक मौलिक प्रोग्रामिंग नियंत्रण संरचना है जो एक निर्दिष्ट स्थिति के सत्य रहने तक कोड के ब्लॉक को '
                  'दोहराती है।',
                  "लूप के सामान्य प्रकारों में 'for' लूप और 'while' लूप शामिल हैं।",
                  'लूप का उपयोग करने से डुप्लिकेट कोड समाप्त होता है और प्रोग्राम को डेटा की सूचियों को कुशलतापूर्वक '
                  'संसाधित करने में मदद मिलती है।']},
 'paris': {'en': ['Paris is the capital and most populous city of France, located along the Seine River.',
                  'It is a global center for art, fashion, gastronomy, and culture, famous for landmarks like the '
                  'Eiffel Tower, the Louvre, and Notre-Dame.',
                  'The city is renowned for its cafe culture and architectural beauty dating back centuries.'],
           'hi': ['पेरिस फ्रांस की राजधानी और सबसे अधिक आबादी वाला शहर है, जो सीन नदी के किनारे स्थित है।',
                  'यह कला, फैशन, पाक कला और संस्कृति का एक वैश्विक केंद्र है, जो एफिल टॉवर, लौवर और नोट्रे-डेम जैसे '
                  'स्थलों के लिए प्रसिद्ध है।',
                  'यह शहर अपनी कैफे संस्कृति और सदियों पुरानी वास्तुकला की सुंदरता के लिए प्रसिद्ध है।']},
 'photosynthesis': {'en': ['Photosynthesis is the process used by plants, algae, and certain bacteria to convert light '
                           'energy into chemical energy.',
                           'It uses carbon dioxide and water to produce glucose and oxygen, which supports almost all '
                           'aerobic life on Earth.',
                           'Chlorophyll, the green pigment in leaves, is responsible for capturing the solar energy '
                           'required for this reaction.'],
                    'hi': ['प्रकाश संश्लेषण वह प्रक्रिया है जिसका उपयोग पौधों, शैवाल और कुछ बैक्टीरिया द्वारा प्रकाश '
                           'ऊर्जा को रासायनिक ऊर्जा में बदलने के लिए किया जाता है।',
                           'यह ग्लूकोज और ऑक्सीजन का उत्पादन करने के लिए कार्बन डाइऑक्साइड और पानी का उपयोग करता है।',
                           'क्लोरोफिल, पत्तियों का हरा वर्णक, इस प्रतिक्रिया के लिए आवश्यक सौर ऊर्जा को पकड़ने के लिए '
                           'जिम्मेदार है।']},
 'python': {'en': ['Python is a high-level, interpreted programming language celebrated for its readability and '
                   'simplicity.',
                   'It supports multiple programming paradigms, including object-oriented, imperative, and functional '
                   'programming.',
                   'With a vast standard library and active ecosystem, it is widely used in web development, data '
                   'science, and artificial intelligence.',
                   'Its clean syntax allows developers to write programs with fewer lines of code than languages like '
                   'C++ or Java.'],
            'hi': ['पायथन एक उच्च-स्तरीय, इंटरप्रिटेड प्रोग्रामिंग भाषा है जो अपनी पठनीयता और सरलता के लिए जानी जाती '
                   'है।',
                   'यह ऑब्जेक्ट-ओरिएंटेड, इंपेरेटिव और फंक्शनल प्रोग्रामिंग सहित कई प्रोग्रामिंग प्रतिमानों का समर्थन '
                   'करती है।',
                   'एक विशाल मानक लाइब्रेरी और सक्रिय पारिस्थितिकी तंत्र के साथ, इसका उपयोग वेब विकास, डेटा विज्ञान और '
                   'एआई में व्यापक रूप से किया जाता है।',
                   'इसका साफ सिंटैक्स डेवलपर्स को सी++ या जावा जैसी भाषाओं की तुलना में कम लाइनों में कोड लिखने की '
                   'अनुमति देता है।'],
            'subtopics': {'popular': {'en': ['Python is popular because of its incredibly gentle learning curve, '
                                             'readable syntax, and massive supportive global community of developers.'],
                                      'hi': ['पायथन अपने अविश्वसनीय रूप से आसान सीखने के मार्ग, पठनीय सिंटैक्स और '
                                             'डेवलपर्स के विशाल वैश्विक समुदाय के कारण लोकप्रिय है।']},
                          'use': {'en': ['Python is heavily used in machine learning (libraries like TensorFlow, '
                                         'PyTorch), data analysis (pandas, numpy), web backends (Django, Flask), and '
                                         'scripting or automation tasks.'],
                                  'hi': ['पायथन का उपयोग मशीन लर्निंग (TensorFlow, PyTorch), डेटा विश्लेषण (pandas, '
                                         'numpy), वेब बैकएंड (Django, Flask) और स्क्रिप्टिंग या स्वचालन कार्यों में '
                                         'बहुत अधिक किया जाता है।']}}},
 'sky blue': {'en': ['The sky appears blue due to a phenomenon called Rayleigh scattering, which describes how '
                     'sunlight scatters in the atmosphere.',
                     "Earth's atmosphere scatters shorter wavelengths of light, such as blue and violet, in all "
                     'directions much more than longer wavelengths like red.',
                     'Although violet light has an even shorter wavelength, our eyes are much more sensitive to blue '
                     'light, so the sky looks blue to us.'],
              'hi': ['आकाश रेले स्कैटरिंग (Rayleigh scattering) नामक घटना के कारण नीला दिखाई देता है, जो बताती है कि '
                     'सूर्य का प्रकाश वातावरण में कैसे बिखरता है।',
                     'पृथ्वी का वायुमंडल लाल जैसी लंबी तरंग दैर्ध्य की तुलना में नीले और बैंगनी जैसे प्रकाश की छोटी '
                     'तरंग दैर्ध्य को सभी दिशाओं में अधिक बिखेरता है।',
                     'हालांकि बैंगनी प्रकाश की तरंग दैर्ध्य और भी छोटी होती है, हमारी आंखें नीले प्रकाश के प्रति अधिक '
                     'संवेदनशील होती हैं, इसलिए आकाश हमें नीला दिखाई देता है।']},
 'sleep': {'en': ['We sleep because it is essential for physiological restoration, cognitive processing, and overall '
                  'brain health.',
                  'During sleep, the body repairs tissues, synthesizes hormones, and strengthens the immune system.',
                  'The brain also consolidates memories, processes information from the day, and clears out cellular '
                  'waste products.'],
           'hi': ['हम सोते हैं क्योंकि यह शारीरिक बहाली, संज्ञानात्मक प्रसंस्करण और समग्र मस्तिष्क स्वास्थ्य के लिए '
                  'आवश्यक है।',
                  'नींद के दौरान, शरीर ऊतकों की मरम्मत करता है, हार्मोन का संश्लेषण करता है और प्रतिरक्षा प्रणाली को '
                  'मजबूत करता है।',
                  'मस्तिष्क यादों को मजबूत करता है, दिन भर की जानकारी कोसंसाधित करता है और कोशिकीय अपशिष्ट उत्पादों को '
                  'साफ करता है।']},
 'speed of light': {'en': ['The speed of light in a vacuum is a universal physical constant exactly equal to '
                           '299,792,458 meters per second.',
                           'It represents the absolute speed limit at which energy, matter, and information can travel '
                           'through space.',
                           'According to special relativity, as an object with mass accelerates towards the speed of '
                           'light, its relativistic mass approaches infinity.'],
                    'hi': ['निर्वात (vacuum) में प्रकाश की गति एक सार्वभौमिक भौतिक स्थिरांक है जो ठीक 299,792,458 मीटर '
                           'प्रति सेकंड के बराबर है।',
                           'यह उस पूर्ण गति सीमा का प्रतिनिधित्व करता है जिस पर ऊर्जा, पदार्थ और जानकारी अंतरिक्ष में '
                           'यात्रा कर सकते हैं।',
                           'विशिष्ट सापेक्षता के अनुसार, जैसे ही द्रव्यमान वाली वस्तु प्रकाश की गति की ओर बढ़ती है, '
                           'उसका द्रव्यमान अनंत की ओर बढ़ जाता है।']},
 'sun': {'en': ['The Sun is the star at the center of the Solar System, comprising about 99.8% of its total mass.',
                'It is a nearly perfect sphere of hot plasma, heated to incandescence by nuclear fusion reactions in '
                'its core.',
                "It provides the light, heat, and energy that drives Earth's weather, ocean currents, and biological "
                'life.'],
         'hi': ['सूर्य सौर मंडल के केंद्र में स्थित तारा है, जिसमें इसके कुल द्रव्यमान का लगभग 99.8% हिस्सा शामिल है।',
                'यह गर्म प्लाज्मा का एक लगभग आदर्श गोला है, जो इसके कोर में परमाणु संलयन प्रतिक्रियाओं द्वारा गर्म '
                'होता है।',
                'यह प्रकाश, गर्मी और ऊर्जा प्रदान करता है जो पृथ्वी के मौसम और जैविक जीवन को संचालित करता है।']},
 'tech': {'en': ['Modern technology relies heavily on the Internet, a global network connecting billions of computers '
                 'and devices worldwide.',
                 'Databases serve as structured storage engines to store, retrieve, and manage massive volumes of '
                 'digital information efficiently.',
                 'Cloud computing allows businesses to access servers, storage, and databases over the internet on a '
                 'flexible, pay-as-you-go basis.',
                 'These interconnected systems form the foundation of our modern digital economy and day-to-day '
                 'software tools.'],
          'hi': ['आधुनिक तकनीक इंटरनेट पर बहुत अधिक निर्भर करती है, जो दुनिया भर के अरबों कंप्यूटरों और उपकरणों को '
                 'जोड़ने वाला एक वैश्विक नेटवर्क है।',
                 'डेटाबेस बड़े पैमाने पर डिजिटल जानकारी को कुशलतापूर्वक संग्रहीत, पुनर्प्राप्त और प्रबंधित करने के लिए '
                 'संरचित स्टोरेज इंजन के रूप में कार्य करते हैं।',
                 'क्लाउड कंप्यूटिंग व्यवसायों को इंटरनेट पर लचीले ढंग से सर्वर, स्टोरेज और डेटाबेस तक पहुंचने की '
                 'अनुमति देता है।',
                 'ये आपस में जुड़े सिस्टम हमारी आधुनिक डिजिटल अर्थव्यवस्था और दैनिक सॉफ्टवेयर टूल की नींव बनाते हैं।'],
          'subtopics': {'internet': {'en': ['The internet is a global system of interconnected computer networks that '
                                            'uses the Internet Protocol suite (TCP/IP) to link devices worldwide.'],
                                     'hi': ['इंटरनेट आपस में जुड़े कंप्यूटर नेटवर्क की एक वैश्विक प्रणाली है जो दुनिया '
                                            'भर के उपकरणों को जोड़ने के लिए इंटरनेट प्रोटोकॉल सूट का उपयोग करती '
                                            'है।']}}},
 'variables': {'en': ["A variable is a symbolic name or container that stores a data value in a computer's memory "
                      'during program execution.',
                      'Variables can hold various data types, such as integers, floating-point numbers, strings, '
                      'booleans, or complex objects.',
                      'The value stored in a variable can be referenced, modified, or updated dynamically as the code '
                      'runs.'],
               'hi': ['वेरिएबल एक प्रतीकात्मक नाम या कंटेनर है जो प्रोग्राम निष्पादन के दौरान कंप्यूटर की मेमोरी में '
                      'डेटा मान संग्रहीत करता है।',
                      'वेरिएबल विभिन्न प्रकार के डेटा रख सकते हैं, जैसे पूर्णांक (integers), दशमलव संख्याएं (floats), '
                      'स्ट्रिंग्स और बूलियन।',
                      'वेरिएबल में संग्रहीत मान को कोड चलने के दौरान गतिशील रूप से संदर्भित, संशोधित या अपडेट किया जा '
                      'सकता है।']}}


KB_SYSTEM_PROMPT_TEMPLATE = ("You are 'OmniChat Knowledge Base Assistant', a helpful AI assistant. Your primary goal is to answer the user's "
 'question using the provided document context below.\n'
 '\n'
 'Instructions:\n'
 '1. Prioritize facts and details from the UPLOADED DOCUMENTS CONTEXT.\n'
 '2. If the answer cannot be found in the context, use your general knowledge to answer the question, but begin your '
 "response with a brief note indicating you are answering from general knowledge (e.g. 'Although not found in the "
 "documents...').\n"
 "3. Keep your answer factual and helpful. Do NOT reply with generic refusals like 'I don't have access to this "
 "information' or 'the documents do not contain...'.\n"
 '\n'
 '--- UPLOADED DOCUMENTS CONTEXT ---\n'
 '{context_str}')


RESEARCH_SYSTEM_PROMPT = ("You are 'OmniChat Research Expert', an expert academic research assistant.\n"
 'Your goal is to help the user formulate hypotheses, review literature, explain scientific methodology, or compile '
 'peer review drafts using precise, clear, and structured academic reasoning.')


