 context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Checking Hotel Availability and Prices for you. Please wait...")
    response = requests.get(
        'http://host.docker.internal:5000/scrape?arrive=2023-09-01&depart=2023-09-05&adults=2&child=2&childages=3|9&rooms=1&hotel_id=64518&currency=IDR')
    hotel_data = response.json()
    print(hotel_data)

    headers = hotel_data[0].keys()
    print(headers)
    table = tabulate.tabulate(hotel_data, headers='keys', tablefmt="grid")
    print(table)

    context.bot.send_message(chat_id=update.effective_chat.id, text=table)