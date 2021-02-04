import scrapy

from scrapy.http import Request
from scrapy.crawler import CrawlerProcess
from scrapy.selector import Selector
from allrecipe.items import AllrecipeItem, IngredientItem
import random
import time
import json


class AllRecipe(scrapy.Spider):


    name = 'allrecipecom'

    # allowed_domains = ['https://www.allrecipe.com']

    base_url = 'http://allrecipes.com/recipes/84/healthy-recipes/?page='

    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    }

    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'allrecipe.spiders.recipemiddleware.RecipeMiddleware': 300
        }
    }
    

    def start_requests(self):
        for page in range(1, 100):
            next_page = self.base_url + str(page)

            yield Request(url=next_page, headers=self.headers, callback=self.parse)

    def parse(self, response):
        for recipe in response.css('div.tout__content'):

            datakey = recipe.css(
                'a.tout__titleLink::attr(href)').extract_first()

            url = "http://allrecipes.com/" + datakey

            yield Request(url, callback=self.parsedetil)

    def parsedetil(self, response):

        title = response.css(
            'div.headline-wrapper > h1::text').extract_first()

        author = response.css(
            'span.author-name-title > a::text').extract_first()

        # Kategory di pipeline dibuat statis
        # category = response.css(
        #     'ol.breadcrumbs__list > li.breadcrumbs__item.breadcrumbs__item--last > a > span::text').extract_first()

        photo = response.css(
            'div.image-container > div::attr(data-src)').extract_first()

        first_paragraph = response.css('.margin-0-auto::text').extract_first()

        ingredients = list()
        for ingredient in response.css('ul.ingredients-section'):
            ingredient_list = ingredient.css(
                '.ingredients-item-name::text').getall()
            ingredients.append(ingredient_list)

        directions = list()
        for direction in response.css('ul.instructions-section'):
            direction_list = direction.css(
                'div.section-body > div > p::text').getall()
            directions.append(direction_list)

        nutrition_facts = response.css(
            'div.partial.recipe-nutrition-section > div.section-body::text').extract_first()

        script = response.xpath(
            "//script[@type='application/ld+json']/text()").get()

        json_data = json.loads(script)

        RecipeItem = AllrecipeItem()

        RecipeItem['title'] = title
        RecipeItem['author'] = author

        # Kategory di pipeline dibuat statis
        # RecipeItem['category'] = category
        RecipeItem['photo'] = photo
        RecipeItem['first_paragraph'] = first_paragraph
        RecipeItem['ingredients'] = ingredients
        RecipeItem['directions'] = directions
        RecipeItem['nutrition_facts'] = nutrition_facts
        RecipeItem['preptime'] = json_data[1]['prepTime']
        RecipeItem['cook_time'] = json_data[1]['cookTime']
        RecipeItem['recipe_yield'] = json_data[1]['recipeYield']
        RecipeItem['date_published'] = json_data[1]['datePublished']
        try:
            RecipeItem['rating_value'] = json_data[1]['aggregateRating']['ratingValue']
            RecipeItem['rating_count'] = json_data[1]['aggregateRating']['ratingCount']
        except KeyError :
                print('value & count not exist')
        RecipeItem['calorie'] = json_data[1]['nutrition']['calories']
        RecipeItem['recipe_ingredient'] = json_data[1]['recipeIngredient']
        RecipeItem['recipe_instructions'] = json_data[1]['recipeInstructions']
        RecipeItem['date_published'] = self.random_date(
            "1/1/2018 1:30 PM", "1/1/2021 4:50 AM", random.random())
        RecipeItem['desc'] = json_data[1]['description']

        yield RecipeItem

    def str_time_prop(self, start, end, format, prop):

        stime = time.mktime(time.strptime(start, format))
        etime = time.mktime(time.strptime(end, format))

        ptime = stime + prop * (etime - stime)

        return time.strftime(format, time.localtime(ptime))

    def random_date(self, start, end, prop):
        return self.str_time_prop(start, end, '%m/%d/%Y %I:%M %p', prop)
