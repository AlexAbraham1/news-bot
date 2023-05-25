import llms
import tweepy
import os


def send_tweet(tweet):
    consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
    consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    client = tweepy.Client(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )
    return client.create_tweet(text=tweet)


def generate_gpt_response(model, prompt) -> str:
    result = model.complete(prompt, temperature=0.8, max_tokens=1000)
    return result.text


def format_gpt_response(response_text: str):
    response_text = response_text.strip()

    response = {
        "tweet": None,
        "hashtags": None
    }
    for line in response_text.split("\n"):
        if line.startswith("Tweet: "):
            response["tweet"] = line[7:]
        elif line.startswith("Hashtags: "):
            response["hashtags"] = line[10:]

    return response


def get_prompt_from_news_article(article_text):
    return """
        Please write a tweet (max 250 characters) summarizing the following article:
        
        {}
    """.format(article_text)

def run():
    model = llms.init(model='gpt-3.5-turbo')

    test = """
    Image: Remedy Entertainment Alan Wake 2 just got an official release date — October 17th — but you won’t be able to buy a physical copy of the game, developer Remedy Entertainment revealed in an FAQ on Wednesday. Remedy has three arguments as to why: it says that many players have shifted to only buying games digitally, not releasing the game on disc keeps the price down, and the studio didn’t want to require a separate download even if it released a disc product. Here’s the company’s full explanation, from the FAQ: Why is Alan Wake 2 a digital-only release? There are many reasons for this. For one, a large number of have shifted to digital only. You can buy a Sony PlayStation 5 without a disc drive and Microsoft’s Xbox Series S is a digital only console. It is... Continue reading…
    """
    prompt = get_prompt_from_news_article(test)

    response = generate_gpt_response(model, prompt)
    print(response)

    # twitter_status = send_tweet(response["tweet"])
    # print(twitter_status)


if __name__ == "__main__":
    run()
