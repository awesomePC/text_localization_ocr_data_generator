from translate import Translator
translator= Translator(from_lang="en",to_lang="ar")
from faker import Faker

faker = Faker()
n = 10
fake_names = {}
for i in range(1,n) :
    name = faker.name()
    translation = translator.translate(name)
    fake_names[i] = name,translation
    
print(fake_names) 
    
