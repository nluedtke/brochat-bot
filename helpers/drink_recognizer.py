from clarifai.rest import ClarifaiApp, Image


def drink_or_not_drink(image_url, clarifai_api_key):

    app = ClarifaiApp(api_key=clarifai_api_key)

    model = app.models.get('food-items-v1.0')
    image = Image(url=image_url)
    response_data = model.predict([image])

    concepts = response_data['outputs'][0]['data']['concepts']

    drinks = [
        'beer',
        'alcohol',
        'cocktail',
        'wine',
        'liquor'
    ]

    print(concepts)

    for concept in concepts:
        for drink in drinks:
            if concept['name'] == drink and concept['value'] > 0.95:
                return True
    else:
        return False

if __name__ == "__main__":

    from sys import argv

    url = argv[1]

    print(drink_or_not_drink(url, 'c64d9922a1b6435da89ee8ac9d696427'))
