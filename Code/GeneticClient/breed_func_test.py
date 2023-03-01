from AiManager import AiManager
from ActionRule import ActionRule
from publisher import Publisher

if __name__ == '__main__':
    ai = AiManager(Publisher)
    a1 = ActionRule()
    a2 = ActionRule()
    a3 = ai.breed_avg(a1,a2)
    print("A1 values: {}\n A2 values:{}\n A3: values{}\n".format(a1.get_conditional_values(), a2.get_conditional_values(), a3.get_conditional_values()))
    print("A1 conditional string: {}\n A2 conditional string: {}\n A3 conditional string: {}\n".format(format(a1.get_cond_bitstr(),'b'), format(a2.get_cond_bitstr(),'b'), format(a3.get_cond_bitstr(),'b')))