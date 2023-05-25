import llms
import tweepy
import os
import feedparser
from bs4 import BeautifulSoup
import re

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


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
    result = model.complete(prompt, temperature=0.4, max_tokens=1000)
    return result.text


def get_mongo_engine():
    uri = "mongodb+srv://{}:{}@{}/?retryWrites=true&w=majority".format(
        os.getenv("MONGO_USER"),
        os.getenv("MONGO_PASS"),
        os.getenv("MONGO_HOST")
    )
    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))

    # Send a ping to confirm a successful connection
    client.admin.command('ping')
    print("INFO: successfuly connected to MongoDB")

    # connect to the news-bot database
    return client['news-bot']


def article_exists(collection, link):
    return collection.find_one({"link": link}) is not None


def get_verge_articles():
    url = "https://www.theverge.com/rss/index.xml"
    feed = feedparser.parse(url)

    articles = []
    for entry in feed.entries:
        content_html = entry.content[0].value
        soup = BeautifulSoup(content_html, 'html.parser')
        content = re.sub('\s+', ' ', soup.get_text()).strip()
        articles.append({
            "headline": entry.title,
            "date": entry.published,
            "link": entry.id,
            "content": content
        })

    return articles

def get_prompt_from_news_article(article_text):
    return """
        Please write a tweet summarizing the following article:
        
        "{}"
        
        The tweet can have a maximum of 200 characters.
    """.format(article_text)

def run():
    # initialize mongodb
    db = get_mongo_engine()
    db_articles = db['articles']

    # get articles from verge
    articles = get_verge_articles()

    # generate tweets for each article with ChatGPT that we haven't seen before
    model = llms.init(model='gpt-3.5-turbo')
    for article in articles:
        if article_exists(db_articles, article["link"]):
            continue

        # generate tweet
        print("Generating Tweet for article: {}".format(article["headline"]))
        prompt = get_prompt_from_news_article(article["content"])
        article["tweet"] = generate_gpt_response(model, prompt)
        article["tweet"] += "\n{}".format(article["link"])
        print(article["tweet"])

        # send tweet
        print("Sending Tweet for article: {}".format(article["headline"]))
        twitter_status = send_tweet(article["tweet"])
        print(twitter_status)

        # store record in database
        db_articles.insert_one(article)


if __name__ == "__main__":
    run()
