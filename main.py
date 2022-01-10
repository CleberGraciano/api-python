from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.error import URLError
from bs4 import BeautifulSoup
import re
import csv

db_connect = create_engine('sqlite:///exemplo.db')
app = Flask(__name__)
api = Api(app)


class Users(Resource):
    def get(self):
        conn = db_connect.connect()
        query = conn.execute("select * from user")
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)

    def post(self):
        conn = db_connect.connect()
        name = request.json['name']
        email = request.json['email']

        conn.execute(
            "insert into user values(null, '{0}','{1}')".format(name, email))

        query = conn.execute('select * from user order by id desc limit 1')
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)

    def put(self):
        conn = db_connect.connect()
        id = request.json['id']
        name = request.json['name']
        email = request.json['email']

        conn.execute("update user set name ='" + str(name) +
                     "', email ='" + str(email) + "'  where id =%d " % int(id))

        query = conn.execute("select * from user where id=%d " % int(id))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)

class UserById(Resource):
    def delete(self, id):
        conn = db_connect.connect()
        conn.execute("delete from user where id=%d " % int(id))
        return {"status": "success"}

    def get(self, id):
        conn = db_connect.connect()
        query = conn.execute("select * from user where id =%d " % int(id))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)

class Movies(Resource):
    def post(self):
        urlSite = request.json['urlSite']
        classContentTitleYear = request.json['classContentTitleYear']
        typeContentTitleYear = request.json['typeContentTitleYear']
        classContentRating = request.json['classContentRating']
        typeContentRating = request.json['typeContentRating']

        csvFileName = 'IMDBRatingTop250.csv'
        regexMovieYear = re.compile('(\d{4})')
        regexUserRating = re.compile('\ ((\d{1,3})((\,|\.)\d{1,3})*)')
        result = []

        try:
            url = urlopen(str(urlSite))
        except HTTPError as error:
            print(error)
        except URLError as error:
            print(error)
        else:
            html = BeautifulSoup(url.read(), "html.parser")
            contentTitleYear = html.find_all(str(typeContentTitleYear), {"class": str(classContentTitleYear)})
            contentRating = html.find_all(str(typeContentRating), {"class": str(classContentRating)})

            with open(csvFileName, 'w') as csvfile:
                # criando o arquivo csv com o delimitador
                fileWriter = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
                # Escrevendo cabeçalho no arquivo
                fileWriter.writerow(['TITLE', 'YEAR', 'IMDB RATING', 'USER RATINGS'])  # HEADER

                for cty, cr in zip(contentTitleYear, contentRating):
                    # titulo do filme
                    movieTitle = (cty.a).text

                    # ano de lançamento, com regex para pegar o valor numerico
                    movieYear = re.search(regexMovieYear, (cty.span).text)

                    # avaliação do IMDB
                    imdbRating = cr.strong.text

                    # avaliações dos usuarios, com regex para pegar apenas valor numerico, excluindo o texto da string obtida.
                    userRating = re.search(regexUserRating, cr.strong['title'])

                    # Com os valores salvo nas variaveis escrevo elas no arquivo
                    fileWriter.writerow([movieTitle, movieYear.group(0), imdbRating, userRating.group(0)])  # CONTENT

                    #print(movieTitle, movieYear.group(0), imdbRating, userRating.group(0))

                    result.append(
                        {
                            "movieTitle" : movieTitle,
                            "movieYear" : movieYear.group(0),
                            "imdbRating" : imdbRating,
                            "userRating" : userRating.group(0)
                        })

        return jsonify(result)

api.add_resource(Users, '/users')
api.add_resource(UserById, '/users/<id>')
api.add_resource(Movies, '/movies')

if __name__ == '__main__':
    app.run()