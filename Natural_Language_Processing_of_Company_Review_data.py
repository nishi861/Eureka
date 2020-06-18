# -*- coding: utf-8 -*-
"""Copy of Natural Language Processing of Company Review Data.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1SNhj8PYcKV2qGy3YhBizyHI_Oo-nk1Jk

# Sentiment Analysis of Employee Review

### This Project is used to understand the main variables affecting the attrition rates in dream companies like Google, Amazon, Facebook and Apple. 

### We will first clean the data and prepare it for processing. We will later conduct some exploratory data analysis to understand the data better. We will then build various models to predict the satisfaction level of an employee.
"""

# Commented out IPython magic to ensure Python compatibility.
|Importing necessary libraries
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns
# %matplotlib inline
from wordcloud import WordCloud

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.naive_bayes import BernoulliNB, MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn import metrics
from sklearn.metrics import roc_auc_score, accuracy_score
from sklearn.pipeline import Pipeline

from bs4 import BeautifulSoup  
import re
import nltk
from nltk.corpus import stopwords 
from nltk.stem.porter import PorterStemmer
from nltk.stem import SnowballStemmer, WordNetLemmatizer
from nltk import sent_tokenize, word_tokenize, pos_tag

import logging
from gensim.models import word2vec
from gensim.models import Word2Vec
from gensim.models.keyedvectors import KeyedVectors

from keras.preprocessing import sequence
from keras.utils import np_utils
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Lambda
from keras.layers.embeddings import Embedding
from keras.layers.recurrent import LSTM, SimpleRNN, GRU
from keras.preprocessing.text import Tokenizer
from collections import defaultdict
from keras.layers.convolutional import Convolution1D
from keras import backend as K
from keras.layers.embeddings import Embedding
nltk.download("punkt")
nltk.download("stopwords")
nltk.download("wordnet")

"""### Loading the Employee Reviews dataset"""

from google.colab import files
uploaded = files.upload()

# Load csv file
data = pd.read_csv('employee_reviews.csv')
# viewing an excerpt of the data
data.head()

"""### Descriptive Analytics for the data"""

#Knowing the data
print("\nTotal number of reviews: ",len(data))
print("\nTotal number of companies: ", len(data['company'].unique()))
print("\nTypes of employee positions: ", len(list(set(data['job-title']))))

"""### Data Cleaning and Feature Engineering"""

#checking data types
data.dtypes

#checking number of nulls in data source
for i in data.columns.values:
    if data[i].isnull().sum() > 0:
        print('{}  {}'.format(i , data[i].isnull().sum()))


#impute values for NULL
data['advice-to-mgmt'] = data['advice-to-mgmt'].fillna('None')

#converting ratings column data type into numeric
convert_dtype = ['work-balance-stars' , 'culture-values-stars' , 'carrer-opportunities-stars',
                     'comp-benefit-stars','senior-mangemnet-stars', 'helpful-count']
for i in convert_dtype: 
    data[i] = data[i].replace('none' , 0)
    data[i] =  data[i].astype(np.float32)

data.dtypes

#describing the States in the data set
data["location"].value_counts()

_#extracting state
def get_state(x):
    if "(" in x:
        x = x.split("(")[1]
        x = x.split(")")[0]
    elif ", " in x:
        x = x.split(", ")[-1]

    return x

data["state"] = data["location"].apply(lambda x: get_state(x))
data.head(3)

#dropping unnecessary columns like links of the reviews
data.drop(columns=['link','Unnamed: 0'], inplace=True)

#extracting the year 
data['year'] = data['dates'].str.split(", ").str[1]

"""### Data Visualization"""

# Plot distribution of rating
plt.figure(figsize=(12,8))
data['overall-ratings'].value_counts().sort_index().plot(kind='bar')
plt.title('Distribution of Rating')
plt.xlabel('Rating')
plt.ylabel('Count')

"""We can see from the above plot that the overall ratings are more positive for the companies."""

# Plot number of reviews for companies
company = data["company"].value_counts()
# brands.count()
plt.figure(figsize=(12,8))
company.plot(kind='bar')
plt.title("Number of Reviews for the 6 Companies")

"""We can see here that amazon has the most number of reviews in the data set , while Netflix hs the least number of reviews submitted."""

# Plot distribution of ratings for each catefgory of ratings given to companies
rating_cols = ["overall-ratings", "work-balance-stars", "culture-values-stars",
       "carrer-opportunities-stars", "comp-benefit-stars",
       "senior-mangemnet-stars"]

sns.reset_defaults()

xcol = "company"
xlabel = "Company"
ylabel = "Count"
title = "Vote Count Per Company"
nrows = 3
ncols = 2
sns.countplot(x=data[xcol], data=data)
#plt.subplot(nrows,ncols, i+1)              
plt.title(title)
plt.xlabel(xlabel)
plt.ylabel(ylabel)
plt.plot()

feature_count = len(rating_cols)

figsize=(20, 16)
ticksize = 14
titlesize = ticksize + 8
labelsize = ticksize + 5

sns.set(context='notebook', style='whitegrid', palette='deep', font='sans-serif', font_scale=1, color_codes=True, rc=None)
sns.set_style("ticks", {"xtick.major.size": ticksize, "ytick.major.size": ticksize})


fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize)
plt.subplots_adjust(hspace=.6, wspace=.3)

params = {'figure.figsize' : figsize,
          'axes.labelsize' : labelsize,
          'axes.titlesize' : titlesize}

plt.rcParams.update(params)

xcol = "company"
xlabel = "Company"
title = "Vote Count Per Company"
sns.countplot(x=data[xcol], data=data)
plt.title(title)
plt.xlabel(xlabel)
plt.ylabel(ylabel)
plt.plot()

feature_count = len(rating_cols)

for i in range(feature_count):
    plt.subplot(nrows,ncols, i+1)
    ylabel = re.sub("[^a-zA-Z]", " ", rating_cols[i])
    ylabel = re.sub("\s+", " ", ylabel).title()
    tmp = data.groupby(xcol, as_index=False)[rating_cols[i]].mean()
    sns.barplot(x=xcol, y=rating_cols[i], data=tmp)
    plt.title(ylabel)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.plot()

plt.show()

"""The above distribution shows the average rating for each category and for each company. We can observe that Facebook has the highest overall rating. Its also the highest in all individual categories. This shows a more positive sentiment towards Facebook."""

# Plot distribution of positive review length
review_length = data["pros"].map(lambda x: len(x.split(" ")))
plt.figure(figsize=(10,8))
review_length.loc[review_length < 150].hist()
plt.title("Distribution of Word count of positive reviews")
plt.xlabel('Word Count')
plt.ylabel('Count')

# Plot distribution of negative review length
review_length = data["cons"].map(lambda x: len(x.split(" ")))
plt.figure(figsize=(10,8))
review_length.loc[review_length < 150].hist()
plt.title("Distribution of Word count of negative reviews")
plt.xlabel('Word Count')
plt.ylabel('Count')

"""In the above two lines we have tried to understand the word count for both positive and negative reviews. We can clearly see that people tend to write more will writing positive reviews.

We will now create a new call which will be used for understanding and predicting the sentiments of the companies.
"""

#classifying ratings as positive or negative
#for overall rating greater than 3 , the sentiment is 1, which is positive
#for overall rating less than or equal to 3, the sentiment is negative, or 0
data['Sentiment'] = np.where(data['overall-ratings'] <= 3,0,1)
data["Sentiment"].value_counts()
#merging the pros and cons columns of the dataset. to further use for prediction 
data["Review"] = data[['pros', 'cons']].apply(lambda x: '.'.join(x), axis=1)
data.head(10)

"""### Predictive Modelling

We will now try and understand the average Baseline accuracy before we begin modelling.
"""

#Base Model
data["Sentiment"].value_counts()


#1 - 45688
#0 - 21841
45688/(21841+45688)

#since majority of the data is positively rated (sentiment = 1), we will clasify all data points as 1
positive = len(data[data["Sentiment"] == 1])
total = len(data["Sentiment"])
accuracy = (positive/total)*100
print('The baseline accuracy is %.2f' %accuracy)

# Split data into training set and validation
X_train, X_test, y_train, y_test = train_test_split(data['Review'], data['Sentiment'], \
                                                    test_size=0.2, random_state=0)

print('Load %d training examples and %d test examples. \n' %(X_train.shape[0],X_test.shape[0]))
print('Show a review in the training set : \n', X_train.iloc[10])

#Defining a function which cleans the data - removes stop words and lemmitizes
def cleanText(raw_text, remove_stopwords=True, lemmetization=True, split_text=False, \
             ):
    '''
    Convert a raw review to a cleaned review
    '''
    #text = BeautifulSoup(raw_text, 'lxml').get_text()  #remove html
    text = raw_text
    letters_only = re.sub("[^a-zA-Z]", " ", text)  # remove non-character
    words = letters_only.lower().split() # convert to lower case 
    
    if remove_stopwords: # remove stopword
        stops = set(stopwords.words("english"))
        words = [w for w in words if not w in stops]
        
    if lemmetization==True: 
        #stemmer = SnowballStemmer('english') 
        #words = [stemmer.stem(w) for w in words]
        # Lemmatizataion
        
        lmtzr = WordNetLemmatizer()
        words = [lmtzr.lemmatize(word) for word in words]

    if split_text==True:  # split text
        return (words)
    
    return( " ".join(words))

# Preprocess text data in training set and validation set
X_train_cleaned = []
X_test_cleaned = []

for d in X_train:
    X_train_cleaned.append(cleanText(d))
print('Show a cleaned review in the training set : \n',  X_train_cleaned[10])
    
for d in X_test:
    X_test_cleaned.append(cleanText(d))

"""We will first train the data using different methods of tokenizers such as CountVectorizer, TFIDF and Word2Vec to create a corpus. We will then predict the trained models on various predictive models such as Naive Bayes, Logistic Regression and Random Forest.

## 1. CountVectorizer
"""

# Fit and transform the training data to a document-term matrix using CountVectorizer

#countvector - tokenizes the text - builds vocabulary - then can make new documents using that vocabulary
countVect = CountVectorizer() 
X_train_countVect = countVect.fit_transform(X_train_cleaned)

print("Number of features : %d \n" %len(countVect.get_feature_names())) #6378 
print("Show some feature names : \n", countVect.get_feature_names()[::1000])

"""Training a Multinomial Naive Bayes model"""

# Train MultinomialNB classifier
mnb = MultinomialNB()
mnb.fit(X_train_countVect, y_train)

def modelEvaluation(predictions):
    '''
    Print model evaluation to predicted result 
    '''
    print ("\nAccuracy on test set: {:.4f}".format(accuracy_score(y_test, predictions)))
    print("\nAUC score : {:.4f}".format(roc_auc_score(y_test, predictions)))
    print("\nConfusion Matrix : \n", metrics.confusion_matrix(y_test, predictions))

# Evaluate the model on validaton set
predictions = mnb.predict(countVect.transform(X_test_cleaned))
modelEvaluation(predictions)

"""Training a Logistic Regression Model"""

# Logistic Regression
lr = LogisticRegression(max_iter=500)
lr.fit(X_train_countVect, y_train)

# Evaluate on the validaton set
predictions = lr.predict(countVect.transform(X_test_cleaned))
modelEvaluation(predictions)

"""## 2. TFIDF Vectorizer"""

# Fit and transform the training data to a document-term matrix using TfidfVectorizer 
tfidf = TfidfVectorizer(min_df=5) #minimum document frequency of 5
X_train_tfidf = tfidf.fit_transform(X_train_cleaned)
print("Number of features : %d \n" %len(tfidf.get_feature_names())) #1722
print("Show some feature names : \n", tfidf.get_feature_names()[::1000])

# Train MultinomialNB classifier
mnb = MultinomialNB()
mnb.fit(X_train_tfidf, y_train)

# Logistic Regression
lr = LogisticRegression(max_iter=500)
lr.fit(X_train_tfidf, y_train)

# Look at the top 10 features with smallest and the largest coefficients
feature_names = np.array(tfidf.get_feature_names())
sorted_coef_index = lr.coef_[0].argsort()
print('\nTop 10 features with smallest coefficients :\n{}\n'.format(feature_names[sorted_coef_index[:10]]))
print('Top 10 features with largest coefficients : \n{}'.format(feature_names[sorted_coef_index[:-11:-1]]))

"""We can observe here that the 10 features with largest coefficients have positive sentiments associated with it. While the smallest coefficients are associated with negative sentiments. This shows that people write more positive reviews and focus more on positive sentiments whike writing workplace reviews."""

# Evaluate on the LR validaton set
predictions = lr.predict(tfidf.transform(X_test_cleaned))
modelEvaluation(predictions)

# Evaluate the MNB model on validaton set 
predictions = mnb.predict(tfidf.transform(X_test_cleaned))
modelEvaluation(predictions)

# Building a pipeline
estimators = [("tfidf", TfidfVectorizer()), ("lr", LogisticRegression(max_iter=500))]
model = Pipeline(estimators)
# Grid search
params = {"lr__C":[0.1, 1, 10], #regularization param of logistic regression
          "tfidf__min_df": [1, 3], #min count of words 
          "tfidf__max_features": [1000, None], #max features
          "tfidf__ngram_range": [(1,1), (1,2)], #1-grams or 2-grams
          "tfidf__stop_words": [None, "english"]} #use stopwords or don't
grid = GridSearchCV(estimator=model, param_grid=params, scoring="accuracy", n_jobs=1)
grid.fit(X_train_cleaned, y_train)
print("The best paramenter set is : \n", grid.best_params_)
# Evaluate on the validaton set
predictions = grid.predict(X_test_cleaned)
modelEvaluation(predictions)

"""## 3. Word2Vec"""

# Split review text into parsed sentences uisng NLTK's punkt tokenizer
tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

def parseSent(review, tokenizer, remove_stopwords=False):
    '''
    Parse text into sentences
    '''
    raw_sentences = tokenizer.tokenize(review.strip())
    sentences = []
    for raw_sentence in raw_sentences:
        if len(raw_sentence) > 0:
            sentences.append(cleanText(raw_sentence, remove_stopwords, split_text=True))
    return sentences


# Parse each review in the training set into sentences
sentences = []
for review in X_train_cleaned:
    sentences += parseSent(review, tokenizer)
    
print('%d parsed sentence in the training set\n'  %len(sentences))
print('Show a parsed sentence in the training set : \n',  sentences[10])

# Fit parsed sentences to Word2Vec model 

num_features = 300  #embedding dimension                     
min_word_count = 5                
num_workers = 4     #4 worker threads for training  
context = 10        #consider 10 words before and after                                                                                  
downsampling = 1e-3 #dilute frequent words

print("Training Word2Vec model ...\n")
w2v = Word2Vec(sentences, workers=num_workers, size=num_features, min_count = min_word_count,\
                 window = context, sample = downsampling)
w2v.init_sims(replace=True)
w2v.save("w2v_300features_10minwordcounts_10context") #save trained word2vec model

print("Number of words in the vocabulary list : %d \n" %len(w2v.wv.index2word)) #4016 
print("Show first 10 words in the vocalbulary list: \n", w2v.wv.index2word[0:10])

# Transfrom the training data into feature vectors

def makeFeatureVec(review, model, num_features):
    '''
    Transform a review to a feature vector by averaging feature vectors of words 
    appeared in that review and in the volcabulary list created
    '''
    featureVec = np.zeros((num_features,),dtype="float32")
    nwords = 0.
    index2word_set = set(model.wv.index2word) #index2word is the volcabulary list of the Word2Vec model
    isZeroVec = True
    for word in review:
        if word in index2word_set: 
            nwords = nwords + 1.
            featureVec = np.add(featureVec, model[word])
            isZeroVec = False
    if isZeroVec == False:
        featureVec = np.divide(featureVec, nwords)
    return featureVec


def getAvgFeatureVecs(reviews, model, num_features):
    '''
    Transform all reviews to feature vectors using makeFeatureVec()
    '''
    counter = 0
    reviewFeatureVecs = np.zeros((len(reviews),num_features),dtype="float32")
    for review in reviews:
        reviewFeatureVecs[counter] = makeFeatureVec(review, model,num_features)
        counter = counter + 1
    return reviewFeatureVecs

# Get feature vectors for training set
X_train_cleaned = []
for review in X_train:
    X_train_cleaned.append(cleanText(review, remove_stopwords=True, split_text=True))
trainVector = getAvgFeatureVecs(X_train_cleaned, w2v, num_features)
print("Training set : %d feature vectors with %d dimensions" %trainVector.shape)


# Get feature vectors for validation set
X_test_cleaned = []
for review in X_test:
    X_test_cleaned.append(cleanText(review, remove_stopwords=True, split_text=True))
testVector = getAvgFeatureVecs(X_test_cleaned, w2v, num_features)
print("Validation set : %d feature vectors with %d dimensions" %testVector.shape)

# Logistic Regression
lr = LogisticRegression(max_iter=500)
lr.fit(trainVector, y_train)
# Evaluate on the validaton set
predictions = lr.predict(testVector)
modelEvaluation(predictions)

# Random Forest Classifier
rf = RandomForestClassifier(n_estimators=100)
rf.fit(trainVector, y_train)
predictions = rf.predict(testVector)
modelEvaluation(predictions)

"""Our last model is running a simple LSTM neural network on the Reviews column."""

top_words = 20000 
maxlen = 100 
batch_size = 32
nb_classes = 2
nb_epoch = 5


# Vectorize X_train and X_test to 2D tensor
tokenizer = Tokenizer(nb_words=top_words) #only consider top 20000 words in the corpus
tokenizer.fit_on_texts(X_train_cleaned)
# tokenizer.word_index #access word-to-index dictionary of trained tokenizer

sequences_train = tokenizer.texts_to_sequences(X_train_cleaned)
sequences_test = tokenizer.texts_to_sequences(X_test_cleaned)

X_train_seq = sequence.pad_sequences(sequences_train, maxlen=maxlen)
X_test_seq = sequence.pad_sequences(sequences_test, maxlen=maxlen)


# one-hot encoding of y_train and y_test
y_train_seq = np_utils.to_categorical(y_train, nb_classes)
y_test_seq = np_utils.to_categorical(y_test, nb_classes)

print('X_train shape:', X_train_seq.shape) 
print('X_test shape:', X_test_seq.shape) 
print('y_train shape:', y_train_seq.shape) 
print('y_test shape:', y_test_seq.shape)

# Construct a simple LSTM
model1 = Sequential()
model1.add(Embedding(top_words, 128, dropout=0.2))
model1.add(LSTM(128, dropout_W=0.2, dropout_U=0.2)) 
model1.add(Dense(nb_classes))
model1.add(Activation('softmax'))
model1.summary()


# Compile LSTM
model1.compile(loss='binary_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])

model1.fit(X_train_seq, y_train_seq, batch_size=batch_size, nb_epoch=nb_epoch, verbose=1)

# Model evluation
score = model1.evaluate(X_test_seq, y_test_seq, batch_size=batch_size)
print('Test loss : {:.4f}'.format(score[0]))
print('Test accuracy : {:.4f}'.format(score[1]))

# get weight matrix of the embedding layer
model1.layers[0].get_weights()[0] # weight matrix of the embedding layer, word-by-dim matrix
print("Size of weight matrix in the embedding layer : ", \
      model1.layers[0].get_weights()[0].shape) 

# get weight matrix of the hidden layer
print("Size of weight matrix in the hidden layer : ", \
      model1.layers[1].get_weights()[0].shape) #weight dim of LSTM - w

# get weight matrix of the output layer
print("Size of weight matrix in the output layer : ", \
      model1.layers[2].get_weights()[0].shape) #weight dim of dense layer

"""Training a LSTM model using Word2Vec"""

# Load trained Word2Vec model
w2v = Word2Vec.load("w2v_300features_10minwordcounts_10context")


# Get Word2Vec embedding matrix
embedding_matrix = w2v.wv.syn0  # embedding matrix, type = numpy.ndarray 
print("Shape of embedding matrix : ", embedding_matrix.shape) 
# w2v.wv.syn0[0] #feature vector of the first word in the volcabulary list

top_words = embedding_matrix.shape[0] #4016
maxlen = 100 
batch_size = 32
nb_classes = 2
nb_epoch = 5


# Vectorize X_train and X_test to 2D tensor
tokenizer = Tokenizer(nb_words=top_words) #only consider top 20000 words in the corpse
tokenizer.fit_on_texts(X_train_cleaned)
# tokenizer.word_index #access word-to-index dictionary of trained tokenizer

sequences_train = tokenizer.texts_to_sequences(X_train_cleaned)
sequences_test = tokenizer.texts_to_sequences(X_test_cleaned)

X_train_seq = sequence.pad_sequences(sequences_train, maxlen=maxlen)
X_test_seq = sequence.pad_sequences(sequences_test, maxlen=maxlen)


# one-hot encoding of y_train and y_test
y_train_seq = np_utils.to_categorical(y_train, nb_classes)
y_test_seq = np_utils.to_categorical(y_test, nb_classes)

print('X_train shape:', X_train_seq.shape) #(27799, 100)
print('X_test shape:', X_test_seq.shape) #(3089, 100)
print('y_train shape:', y_train_seq.shape) #(27799, 2)
print('y_test shape:', y_test_seq.shape) #(3089, 2)

# Construct Word2Vec embedding layer
embedding_layer = Embedding(embedding_matrix.shape[0], #4016
                            embedding_matrix.shape[1], #300
                            weights=[embedding_matrix])


# Construct LSTM with Word2Vec embedding
model2 = Sequential()
model2.add(embedding_layer)
model2.add(LSTM(128, dropout_W=0.2, dropout_U=0.2)) 
model2.add(Dense(nb_classes))
model2.add(Activation('softmax'))
model2.summary()

# Compile model
model2.compile(loss='binary_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])

model2.fit(X_train_seq, y_train_seq, batch_size=batch_size, nb_epoch=nb_epoch, verbose=1)


# Model evaluation
score = model2.evaluate(X_test_seq, y_test_seq, batch_size=batch_size)
print('Test loss : {:.4f}'.format(score[0]))
print('Test accuracy : {:.4f}'.format(score[1]))

# get weight matrix of the embedding layer
print("Size of weight matrix in the embedding layer : ", \
      model2.layers[0].get_weights()[0].shape)

# get weight matrix of the hidden layer
print("Size of weight matrix in the hidden layer : ", \
      model2.layers[1].get_weights()[0].shape) #  weight dim of LSTM - w

# get weight matrix of the output layer
print("Size of weight matrix in the output layer : ", \
      model2.layers[2].get_weights()[0].shape) #weight dim of dense layer

"""Lastly, we will create a Word Cloud to visually understand the sentiments of the employees and ex-employees of the six companies. This will show us the most prominent words used to describe positives and negatives of a company."""

def create_word_cloud(sentiment,company):
    '''
    Using WordCloud to understand the overall sentiment of 
    employees for each company
    '''
    try: 
        #data_review = data.loc[data["company"]==brand]
        data_review = data[["Review","Sentiment","company","pros","cons"]]
        data_review = data_review[data_review["company"]==company]
        #Takes 10% of the data
        data_review_sample = data_review
        word_cloud_collection = ''
        
        if sentiment == 1:
            df_reviews = data_review_sample[data_review_sample["Sentiment"]==1]["pros"]
            
        if sentiment == 0:
            df_reviews = data_review_sample[data_review_sample["Sentiment"]==0]["cons"]
            
        for val in df_reviews.str.lower():
            tokens = nltk.word_tokenize(val)
            tokens = [word for word in tokens if word not in stopwords.words('english') and word != "n't"]
            for words in tokens:
                word_cloud_collection = word_cloud_collection + words + ' '

        wordcloud = WordCloud(max_font_size=50,min_font_size=10, width=500, height=300).generate(word_cloud_collection)
        plt.figure(figsize=(10,10))
        plt.imshow(wordcloud)
        plt.axis("off")
        plt.show()
    except: 
        pass

create_word_cloud(sentiment=1,company="google")

create_word_cloud(sentiment=0,company="google")

create_word_cloud(sentiment=1,company="amazon")

create_word_cloud(sentiment=0,company="amazon")

create_word_cloud(sentiment=1,company="netflix")

create_word_cloud(sentiment=0,company="netflix")

create_word_cloud(sentiment=1,company="microsoft")

create_word_cloud(sentiment=0,company="microsoft")

create_word_cloud(sentiment=1,company="facebook")

create_word_cloud(sentiment=0,company="facebook")

create_word_cloud(sentiment=1,company="apple")

create_word_cloud(sentiment=0,company="apple")