"""Grade patch for Calstate LA 2020 Fall midterm3, SW XBlock question
"""

import logging
log = logging.getLogger(__name__)

CALSTATELA_MIDTERM3_ASSIGNMENTS = [
    u"Fall 2020 1081 Midterm 3",
    u"Fall 2020 1082 Midterm 3"
]
CALSTATELA_MIDTERM3_COURSE_KEYS = [
    u"course-v1:CalStateLA+MATH1081_2513+Fall2020_Chavez_TTR1050-1205",
    u"course-v1:CalStateLA+MATH1081_26f3+Fall2020_Zhang_TTR1050-1205",
    u"course-v1:CalStateLA+MATH1081_5936+Fall2020_Piapakdee_TTR0800-0915",
    u"course-v1:CalStateLA+MATH1081_6480+Fall2020_Garcia_TTR0800-0915",
    u"course-v1:CalStateLA+MATH1081_6ee5+Fall2020_Hajaiej_TTR1340-1455",
    u"course-v1:CalStateLA+MATH1081_8e34+Fall2020_Yu_TTR1050-1205",
    u"course-v1:CalStateLA+MATH1081_a2fa+Fall2020_Hajaiej_TTR1215-1330",
    u"course-v1:CalStateLA+MATH1081_acb8+Fall2020_Staff_TTR0925-1040",
    u"course-v1:CalStateLA+MATH1081_b8d5+Fall2020_Staff_MW1340-1455",
    u"course-v1:CalStateLA+MATH1081_bbd1+Fall2020_Flores_TTR0925-1040",
    u"course-v1:CalStateLA+MATH1081_ede2+Fall2020_Choi_MW1215-1330",
    u"course-v1:CalStateLA+MATH1081_f1e9+Fall2020_Staff_TTR1340-1455",
    u"course-v1:CalStateLA+MATH1082_15a8+Fall2020_AlFares_MTWTR1530-1608",
    u"course-v1:CalStateLA+MATH1082_20a3+Fall2020_Staff_MWF1600-1650",
    u"course-v1:CalStateLA+MATH1082_2cd3+Fall2020_Saikaly_MWF1000-1050",
    u"course-v1:CalStateLA+MATH1082_3143+Fall2020_Staff_MWF1600-1650",
    u"course-v1:CalStateLA+MATH1082_3b14+Fall2020_Sam_MTWTR1400-1438",
    u"course-v1:CalStateLA+MATH1082_5158+Fall2020_Yamashita_MWF0800-0850",
    u"course-v1:CalStateLA+MATH1082_5800+Fall2020_Yamashita_MWF1000-1050",
    u"course-v1:CalStateLA+MATH1082_65e9+Fall2020_Saikaly_MWF1200-1250",
    u"course-v1:CalStateLA+MATH1082_986f+Fall2020_Staff_MWF0800-0850",
    u"course-v1:CalStateLA+MATH1082_9c69+Fall2020_Sam_MTWTR1230-1308",
    u"course-v1:CalStateLA+MATH1082_9f24+Fall2020_Chan_MTWTR0800-0838",
    u"course-v1:CalStateLA+MATH1082_a36a+Fall2020_PhanYamada_MWF1400-1450",
    u"course-v1:CalStateLA+MATH1082_b530+Fall2020_Yamashita_MWF1200-1250",
    u"course-v1:CalStateLA+MATH1082_c806+Fall2020_AlFares_MTWTR1100-1138",
    u"course-v1:CalStateLA+MATH1082_d15c+Fall2020_Sam_MTWTR1530-1608",
    u"course-v1:CalStateLA+MATH1082_da74+Fall2020_Jeong_MWF1400-1450"
]
CALSTATELA_MIDTERM3_SWXBLOCK_GRADES_ORIG = {
    '0c76d3b73d34d6b9e3412ee6f7f679': 1,
    '22ab0f912036adc20a8711b7ba059c': 0,
    'fc48c3df0a1ab15a4792a331949548': 0.916666666666666,
    '_653561_': 0.916666666666666,
    '_672763_': 0.916666666666666,
    '_672798_': 0.916666666666666,
    '_672804_': 0.916666666666666,
    '_672840_': 0.916666666666666,
    '6069844d0bff395a3e7d5df67e83ce': 0.916666666666666,
    '8cb7d1622469d5e336e732020f4a92': 1,
    'b6c214fad6d153d47d76d3e099d502': 0.916666666666666,
    'ec6b8b40d6898d48a3a8382dfa1b72': 1,
    '_619992_': 0.916666666666666,
    '_673351_': 0.916666666666666,
    '_673359_': 1,
    '087a70c5397e0ef92b7b0e3c05dd5f': 1,
    'cf283369be944b513bafc2df1fa916': 0.666666666666666,
    '5825690d6912727a0a619f588f8ad7': 0,
    '8d474c543af962039a1a743e358ebb': 0.916666666666666,
    'ab829dd958ad1a6e10c3936acdf90e': 0,
    'dd2ee2ff1cc56cb127e8f77accc92b': 1,
    '_655630_': 1,
    '277ce1346ba35ac22fa74d7a6b1374': 1,
    '2a85fc9ebf68e299f47b818ce9a546': 1,
    '30e5dc9799623e33fcb0f753083d49': 0.916666666666666,
    'f74ebd6ddd91c796624b58e7e2e5a7': 1,
    '46027a4b453fc816808b7196bf60b9': 0.916666666666666,
    '5c0b240a8294c08119a44fa4604031': 0.916666666666666,
    'ae33f76b65c3bd73499c5f63c19049': 0.916666666666666,
    '15af5a6344522e03059fdbdeb6ba85': 1,
    '363975031004cfe1d5f32cc24a9415': 0.916666666666666,
    '3b04282302b23d65c7533a0478d5a8': 1,
    '433d6e6e1bcb9260ac51aa04842e11': 1,
    '655796e67bd26e19e77fc5271007f7': 1,
    '6f3af09d12182d2fb7abd60af9d760': 0.916666666666666,
    '98db245c9c23eb9e74faa96f965d3c': 0.916666666666666,
    'aa35c217fe6794c28583036b027b7e': 0.916666666666666,
    '_711051_': 0.916666666666666,
    '9b726a84d368afc767933880c8651e': 1,
    'f5a39558b39c688b090e0c76d05ae6': 1,
    '1585553b643a74371b53811acaf3be': 1,
    '24aab1efb705259bf6afffed72c9bc': 0.916666666666666,
    '4d7560f3633ab237c83566c3229c0c': 0.916666666666666,
    '6f5d1b5b9555a7c2d5ea99cb357562': 0.916666666666666,
    '_620820_': 1,
    '_654710_': 1,
    '_671540_': 0.916666666666666,
    'a8a5fd24c714931e1e95e33017d909': 0.916666666666666,
    'f19c748bbc19c90f7f8bfa2138c820': 0.916666666666666,
    '2e367c55c4107bd66ebc0fc663a83f': 0.916666666666666,
    '734ade770d89543c088b52090cf947': 1,
    '74cdcf0ead212b495409d3884e8482': 0.666666666666666,
    '811cd5aaeecc3ed595dec592522b14': 0.666666666666666,
    '8e393fc787c74f18a8ecb8734e43ac': 0.666666666666666,
    'cb2821b15973e4e02bb3706b3471bc': 0.916666666666666,
    'cea7ca94ed1e13735e1e87291dc50a': 0.916666666666666,
    'cf060479c74fe4cd5f4c8c6a5f1032': 0.916666666666666,
    'd5cccbb83f85c0d39283b76ae4bcbb': 0.916666666666666,
    '00e55c8f7f5dbf6340b5812840b0f1': 1,
    '04060f2cd3db5973e6db0fd23b6771': 0.916666666666666,
    '2062d4ce118a8581ffecbdeeeabb15': 1,
    '6c4aad72056cf13de3966981d75198': 1,
    '6e33107cc5d0ca20a54511ecdd55b7': 0.916666666666666,
    'a1ee057b9f47d5c1d6dc59e91a778d': 1,
    'c0c3333d739e5c80267b4ba4a6f556': 0.916666666666666,
    '_654961_': 1,
    '4dfc098cfa032642de477e63c277ab': 0.666666666666666,
    '982d95cec96ccdc5dbcd172d590df3': 0.916666666666666,
    '_658990_': 0.916666666666666,
    '32c379d5abbf3c4664d4bdec67588f': 0.916666666666666,
    '370fb02db7990967b6c84e26267344': 0.916666666666666,
    '40e5db133616795a831f0f2b15e764': 0.916666666666666,
    'df7e49882071c678bcdfde606298cf': 0.916666666666666,
    '_339757_': 0.916666666666666,
    '076915ab3cda7bc2946ca285ccc3da': 0.916666666666666,
    '1933e38cf2f3c987d6aa388df65ff7': 0.916666666666666,
    '673220a299adbc914db25e670a79a5': 0.916666666666666,
    '75df987a9f7c02621eeb046c43b6a8': 1,
    '9eb5aeab7bd72872dfff584bffc0f0': 0,
    'ba182bf23ec22e09d58f3c1d51ef7a': 0.916666666666666,
    '_653132_': 0.916666666666666,
    '02235c0636974d2045afe70684d430': 1,
    '14b112b5126938c4bb0d119c26cd04': 0.916666666666666,
    '199a8e282433f3071a9cf7552494d6': 0.916666666666666,
    '27d857907826f1de8cf609dddb2c20': 1,
    '391c7bf3c483577beaf524911639b8': 0.916666666666666,
    '7aaa4a9243b0e36485f607a5ca6610': 0.666666666666666,
    'b716fe1b4be3747b397468a51539d8': 1,
    'c7425b6a2c038224e5846579b581a3': 1,
    'd99a6acb8bef2c9dca037b59a21371': 1,
    'e7769fc1563c7734cd8dcaac460fdc': 0.916666666666666,
    'ffbf5bc79afed6815ea386e5c0daa0': 1,
    '019b74278bebad48e683f5673b2f0d': 0.916666666666666,
    '2614dc6b2e14449b5b24d93cbf870b': 0.666666666666666,
    'e92c487bd28147428347455ddecb31': 0.916666666666666,
    '22e6d864e8f3095ac01dd214a2933a': 0.916666666666666,
    '54049d7f651bd5e7b637640ff8d58c': 0.916666666666666,
    '7458cb558a251cb92d0dd4d2abe109': 0.916666666666666,
    '88e8b451fe2585f565b91ebad79ae5': 0.916666666666666,
    '8e36c9522b27e1ac75fb37e9b41815': 0.666666666666666,
    '93f3e2977cca5303f7497fc233cf99': 0.916666666666666,
    'a1b89530eb66c23f9899ae402cf4da': 0.916666666666666,
    'a5f7031d8124184a6e5043db87c5ed': 0.916666666666666,
    '262be90d99dd889b9c0bf8066a0ecb': 0.916666666666666,
    '5e8b7095b8da8e0771be6032888d49': 0.916666666666666,
    'aaaa99f3f1d898b08c3d76d537d336': 0.916666666666666,
    '0378ca43a57102970a566816e033d0': 1,
    'a2e1683cc31fe19a99e190416acdf3': 0.916666666666666,
    'f8da387ac151da01ddcd788bc8df2f': 0.916666666666666,
    '57096a24bb3833a117adcdb71ff9b5': 0.916666666666666,
    'bd90e528e42c91d6b51e0f235dc7b1': 0.916666666666666,
    'd4d1d8265c84a643af244212ea6bbe': 0.916666666666666,
    'e939c29bf957d86d2e13fcf7caddfa': 0,
    'ebe3fcee510caec912249b9639099a': 1,
    '03723fbd43738a001a18120be0f931': 0,
    '6c4aad72056cf13de3966981d75198': 1,
    'b555bd36bcce7a5596b4cc142d91ee': 0.916666666666666,
    '_337932_': 1,
    '10f98f9de1fda472dcc930e93edd1e': 1,
    'af5d32e2dcd5edb73f81d941093d79': 1,
    'ecd06f5325f38ab9888becae9838dd': 1,
    'fdb6108a134f65a747542c177577be': 1,
    '21f0bfbc955c16ea514d4e3968b636': 1,
    '52f2dabc64607c99cbb1fb49b6aafe': 1,
    '8c6c29d1aba73b49df8054e64451bb': 0.916666666666666,
    'abe444752319b372cec06f73cf9034': 0.916666666666666,
    'c06b182504ce551faa5dbd42c1dc1f': 0.916666666666666,
    'd138f8d9a6593c6c371a1566c52458': 0.916666666666666
}
CALSTATELA_MIDTERM3_SWXBLOCK_GRADES_ADJUSTED = {
    '0c76d3b73d34d6b9e3412ee6f7f679': 1,
    '22ab0f912036adc20a8711b7ba059c': 0,
    'fc48c3df0a1ab15a4792a331949548': 0.916666666666666,
    '_653561_': 0.916666666666666,
    '_672763_': 0.916666666666666,
    '_672798_': 0.916666666666666,
    '_672804_': 0.916666666666666,
    '_672840_': 0.916666666666666,
    '6069844d0bff395a3e7d5df67e83ce': 0.916666666666666,
    '8cb7d1622469d5e336e732020f4a92': 1,
    'b6c214fad6d153d47d76d3e099d502': 0.916666666666666,
    'ec6b8b40d6898d48a3a8382dfa1b72': 1,
    '_619992_': 0.916666666666666,
    '_673351_': 0.916666666666666,
    '_673359_': 1,
    '087a70c5397e0ef92b7b0e3c05dd5f': 1,
    'cf283369be944b513bafc2df1fa916': 0.666666666666666,
    '5825690d6912727a0a619f588f8ad7': 0,
    '8d474c543af962039a1a743e358ebb': 0.916666666666666,
    'ab829dd958ad1a6e10c3936acdf90e': 0,
    'dd2ee2ff1cc56cb127e8f77accc92b': 1,
    '_655630_': 1,
    '277ce1346ba35ac22fa74d7a6b1374': 1,
    '2a85fc9ebf68e299f47b818ce9a546': 1,
    '30e5dc9799623e33fcb0f753083d49': 1,
    'f74ebd6ddd91c796624b58e7e2e5a7': 1,
    '46027a4b453fc816808b7196bf60b9': 0.916666666666666,
    '5c0b240a8294c08119a44fa4604031': 0.916666666666666,
    'ae33f76b65c3bd73499c5f63c19049': 0.916666666666666,
    '15af5a6344522e03059fdbdeb6ba85': 1,
    '363975031004cfe1d5f32cc24a9415': 0.916666666666666,
    '3b04282302b23d65c7533a0478d5a8': 1,
    '433d6e6e1bcb9260ac51aa04842e11': 1,
    '655796e67bd26e19e77fc5271007f7': 1,
    '6f3af09d12182d2fb7abd60af9d760': 0.916666666666666,
    '98db245c9c23eb9e74faa96f965d3c': 0.916666666666666,
    'aa35c217fe6794c28583036b027b7e': 0.916666666666666,
    '_711051_': 0.916666666666666,
    '9b726a84d368afc767933880c8651e': 1,
    'f5a39558b39c688b090e0c76d05ae6': 1,
    '1585553b643a74371b53811acaf3be': 1,
    '24aab1efb705259bf6afffed72c9bc': 1,
    '4d7560f3633ab237c83566c3229c0c': 1,
    '6f5d1b5b9555a7c2d5ea99cb357562': 1,
    '_620820_': 1,
    '_654710_': 1,
    '_671540_': 0.916666666666666,
    'a8a5fd24c714931e1e95e33017d909': 0.916666666666666,
    'f19c748bbc19c90f7f8bfa2138c820': 0.916666666666666,
    '2e367c55c4107bd66ebc0fc663a83f': 0.916666666666666,
    '734ade770d89543c088b52090cf947': 1,
    '74cdcf0ead212b495409d3884e8482': 0.666666666666666,
    '811cd5aaeecc3ed595dec592522b14': 0.666666666666666,
    '8e393fc787c74f18a8ecb8734e43ac': 0.666666666666666,
    'cb2821b15973e4e02bb3706b3471bc': 0.916666666666666,
    'cea7ca94ed1e13735e1e87291dc50a': 0.916666666666666,
    'cf060479c74fe4cd5f4c8c6a5f1032': 0.916666666666666,
    'd5cccbb83f85c0d39283b76ae4bcbb': 0.916666666666666,
    '00e55c8f7f5dbf6340b5812840b0f1': 1,
    '04060f2cd3db5973e6db0fd23b6771': 0.916666666666666,
    '2062d4ce118a8581ffecbdeeeabb15': 1,
    '6c4aad72056cf13de3966981d75198': 1,
    '6e33107cc5d0ca20a54511ecdd55b7': 0.916666666666666,
    'a1ee057b9f47d5c1d6dc59e91a778d': 1,
    'c0c3333d739e5c80267b4ba4a6f556': 0.916666666666666,
    '_654961_': 1,
    '4dfc098cfa032642de477e63c277ab': 0.666666666666666,
    '982d95cec96ccdc5dbcd172d590df3': 0.916666666666666,
    '_658990_': 0.916666666666666,
    '32c379d5abbf3c4664d4bdec67588f': 0.916666666666666,
    '370fb02db7990967b6c84e26267344': 0.916666666666666,
    '40e5db133616795a831f0f2b15e764': 0.916666666666666,
    'df7e49882071c678bcdfde606298cf': 0.916666666666666,
    '_339757_': 0.916666666666666,
    '076915ab3cda7bc2946ca285ccc3da': 0.916666666666666,
    '1933e38cf2f3c987d6aa388df65ff7': 0.916666666666666,
    '673220a299adbc914db25e670a79a5': 0.916666666666666,
    '75df987a9f7c02621eeb046c43b6a8': 1,
    '9eb5aeab7bd72872dfff584bffc0f0': 0,
    'ba182bf23ec22e09d58f3c1d51ef7a': 0.916666666666666,
    '_653132_': 0.916666666666666,
    '02235c0636974d2045afe70684d430': 1,
    '14b112b5126938c4bb0d119c26cd04': 0.916666666666666,
    '199a8e282433f3071a9cf7552494d6': 0.916666666666666,
    '27d857907826f1de8cf609dddb2c20': 1,
    '391c7bf3c483577beaf524911639b8': 0.916666666666666,
    '7aaa4a9243b0e36485f607a5ca6610': 0.666666666666666,
    'b716fe1b4be3747b397468a51539d8': 1,
    'c7425b6a2c038224e5846579b581a3': 1,
    'd99a6acb8bef2c9dca037b59a21371': 1,
    'e7769fc1563c7734cd8dcaac460fdc': 0.916666666666666,
    'ffbf5bc79afed6815ea386e5c0daa0': 1,
    '019b74278bebad48e683f5673b2f0d': 0.916666666666666,
    '2614dc6b2e14449b5b24d93cbf870b': 0.666666666666666,
    'e92c487bd28147428347455ddecb31': 0.916666666666666,
    '22e6d864e8f3095ac01dd214a2933a': 0.916666666666666,
    '54049d7f651bd5e7b637640ff8d58c': 0.916666666666666,
    '7458cb558a251cb92d0dd4d2abe109': 0.916666666666666,
    '88e8b451fe2585f565b91ebad79ae5': 0.916666666666666,
    '8e36c9522b27e1ac75fb37e9b41815': 0.666666666666666,
    '93f3e2977cca5303f7497fc233cf99': 0.916666666666666,
    'a1b89530eb66c23f9899ae402cf4da': 0.916666666666666,
    'a5f7031d8124184a6e5043db87c5ed': 0.916666666666666,
    '262be90d99dd889b9c0bf8066a0ecb': 0.916666666666666,
    '5e8b7095b8da8e0771be6032888d49': 0.916666666666666,
    'aaaa99f3f1d898b08c3d76d537d336': 0.916666666666666,
    '0378ca43a57102970a566816e033d0': 1,
    'a2e1683cc31fe19a99e190416acdf3': 0.916666666666666,
    'f8da387ac151da01ddcd788bc8df2f': 0.916666666666666,
    '57096a24bb3833a117adcdb71ff9b5': 0.916666666666666,
    'bd90e528e42c91d6b51e0f235dc7b1': 0.916666666666666,
    'd4d1d8265c84a643af244212ea6bbe': 0.916666666666666,
    'e939c29bf957d86d2e13fcf7caddfa': 0,
    'ebe3fcee510caec912249b9639099a': 1,
    '03723fbd43738a001a18120be0f931': 0,
    '6c4aad72056cf13de3966981d75198': 1,
    'b555bd36bcce7a5596b4cc142d91ee': 0.916666666666666,
    '_337932_': 1,
    '10f98f9de1fda472dcc930e93edd1e': 1,
    'af5d32e2dcd5edb73f81d941093d79': 1,
    'ecd06f5325f38ab9888becae9838dd': 1,
    'fdb6108a134f65a747542c177577be': 1,
    '21f0bfbc955c16ea514d4e3968b636': 1,
    '52f2dabc64607c99cbb1fb49b6aafe': 1,
    '8c6c29d1aba73b49df8054e64451bb': 0.916666666666666,
    'abe444752319b372cec06f73cf9034': 0.916666666666666,
    'c06b182504ce551faa5dbd42c1dc1f': 0.916666666666666,
    'd138f8d9a6593c6c371a1566c52458': 0.916666666666666
}


def calstatela_midterm3_patch_grade(data):
    """
     Dec-2020
     Emergency patch to adjust point value of 1 stepwise problem that was included in
     midterm exam 3 at Cal State LA.

     There is one SWXBlock problem in which the point value is incorrectly reported as 1 point
     but should be 6 points. We need to gross up the point value for this problem by
       a.) subtracting the earned reported points (a value between 0 and 1)
       b.) add the correct grossed up point (a value between 0 and 6)

    Payload format:
        data = {
            'score': 39.91666666666667, 
            'points_possible': 49.0, 
            'user_id': '5825690d6912727a0a619f588f8ad75d69ebae90", 
            'result_date': '2020-12-08T00:45:54.606752+00:00", 
            'activity_id': 'd79c1e0244ff4db180c7bdfce53d9dd8", 
            'type': 'result", 
            'id': 'd79c1e0244ff4db180c7bdfce53d9dd8:5825690d6912727a0a619f588f8ad75d69ebae90'
            }

    """
    log.info('lti_consumers.patches.calstatela_2020midterm3_patch_001.calstatela_midterm3_patch_grade() - data: {data}'.format(
        data=data
    ))

    # we're anticipating that for these three problems
    # we're going to see points_possible == 1 whereas it is supposed to be points_possible == 6
    # assuming that this is the case, we need to amplify the earned score by a multiple of 6.
    if data['points_possible'] == 49:
        log.info('lti_consumers.patches.calstatela_2020midterm3_patch_001.calstatela_midterm3_patch_grade() - patching.')


        # the score 
        username = data['user_id']

        # the awarded score for the midterm exam
        score = float(data['score'])

        # the point value awarded for the SW Xblock problem
        points_awarded = float(CALSTATELA_MIDTERM3_SWXBLOCK_GRADES_ORIG[username])

        # this list considers course sections in which the instructor elected to 
        # gift all 6 possible points to students.
        points_adjusted = float(CALSTATELA_MIDTERM3_SWXBLOCK_GRADES_ADJUSTED[username])

        # subtract the original point value awarded 
        score -= points_awarded

        # add the grossed up point value
        score += (points_adjusted * 6)

        data['score'] = score
        data['points_possible'] = 54

        log.info('lti_consumers.patches.calstatela_2020midterm3_patch_001.calstatela_midterm3_patch_grade() - patched results: {data}'.format(
            data=data
        ))
    return data


def calstatela_midterm3_patch_column(data):
    """
     Dec-2020
     Emergency patch to adjust point value of 1 stepwise problem that was included in
     midterm exam 3 at Cal State LA. 
    
     this method corrects the overall point value of the grade column

    Payload format:
        data = {
            'type': 'activity", 
            'due_date': '2020-12-07T02:59:00+00:00", 
            'points_possible': 49.0, 
            'title': 'Fall 2020 1081 Midterm 3", 
            'id': 'd79c1e0244ff4db180c7bdfce53d9dd8", 
            'description': 'Fall 2020 1081 Midterm 3'
        }
    """
    log.info('lti_consumers.patches.calstatela_2020midterm3_patch_001.calstatela_midterm3_patch_column() - data: {data}'.format(
        data=data
    ))

    if (float(data['points_possible']) != 54.0):
        log.info('lti_consumers.patches.calstatela_2020midterm3_patch_001.calstatela_midterm3_patch_column() - patching.')
        data['points_possible'] = 54.0

    log.info('lti_consumers.patches.calstatela_2020midterm3_patch_001.calstatela_midterm3_patch_column() - patched results: {data}'.format(
        data=data
    ))
    return data

