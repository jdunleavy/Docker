#%% [markdown]
# Content stored \\files2.erpint.pmi.org\KAS\AssetCache as HTML files.  Will have to iterate through folder structure and parse HTML into strings

#%%
import os, logging, re
from bs4 import BeautifulSoup

#%%
def parse_page(page):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(page)
    content = ''

    # extract title text
    header_list = soup.find(class_='header')
    regex = re.compile('^title')
    header_list_items = soup.find_all('h', attrs={'class': regex})

    for h in header_list_items:
        content += h.getText().split('\n')[0] + ' '


    # extract body text
    content_list = soup.find(class_='content')
    content_list_items = soup.find_all('p')
    # regex = re.compile('indent')
    # content_list_items = soup.find_all('p', attrs={'class': regex})

    for p in content_list_items:
        content += p.getText().split('\n')[0] + ' '
    
    return content



#%%
def text_prep(text, 
              tolower=True,
              fixcontractions=True,
              lemmatize=True,
              stopwords=True,
              allowed_tags=re.compile('(NN|VB|JJ|RB}IN)'), 
              minlen=2, 
              maxlen=15):
    """
        text: a string
        
        return: modified initial string
    """
    import re, gensim
    
    REPLACE_BY_SPACE = re.compile('—[/(){}\[\]\|@,;]')
    BAD_SYMBOLS = re.compile('[^0-9a-z #+_]')

    # lowercase
    if tolower:
        try:
            text = text.lower()
        except Exception as e:
            logging.exception(e)
            raise SystemExit('Error converting case. See the log for details.')
    
    # strip html tags
    try:
        text = gensim.parsing.strip_tags(text)
    except Exception as e:
        logging.exception(e)
        raise SystemExit('Error stripping html. See the log for details.')
    
    # replace REPLACE_BY_SPACE symbols by space in text
    try:
        text = re.sub(REPLACE_BY_SPACE, ' ', text)
    except Exception as e:
        logging.exception(e)
        raise SystemExit('Error in REPLACE_BY_SPACE. See the log for details.')
    
    # replace contractions
    if fixcontractions:
        import contractions
        try:
            text = contractions.fix(text)
        except Exception as e:
            logging.exception(e)
            raise SystemExit('Error expanding contractions. See the log for details.')
            
    # delete symbols which are in BAD_SYMBOLS from text
    try:
        text = re.sub(BAD_SYMBOLS, ' ', text)
    except Exception as e:
        logging.exception(e)
        raise SystemExit('Error replacing BAD_SYMBOLS. See the log for details.')
    
    # lemmatize - see hacky workaround for StopIteration error: https://github.com/clips/pattern/issues/243
    if lemmatize:
        import pattern
        try: 
            parsed = pattern.en.parse(text, lemmata=True, collapse=False)
            text = ''
            for sentence in parsed:
                for token, tag, _, _, lemma in sentence:
                    if minlen <= len(lemma) <= maxlen and not lemma.startswith('_'):
                        if allowed_tags.match(tag):
                            text += lemma + ' '
        except Exception as e:
            logging.exception(e)
            raise SystemExit('Error lemmatizing. See the log for details.')
    
    # remove stopwords
    if stopwords:
        try:
            text = gensim.parsing.preprocessing.remove_stopwords(text)
        except Exception as e:
            logging.exception(e)
            raise SystemExit('Error removing stopwords. See the log for details.')
    
    return text



#%%
path = '//files2.erpint.pmi.org/KAS/AssetCache'


#%%
from bs4 import BeautifulSoup
import re, gensim, pattern, time, csv
import pandas as pd
import timeit

df = pd.DataFrame()

start = timeit.default_timer()

with open(os.path.join(os.getcwd(),'assetcrawl.csv'), 'w') as outfile:
    for root, dirs, files in os.walk(path):
        for fname in filter(lambda fname: fname.endswith('.html'), files):
            # pause script to not overload server - 
            # assuming 5000 articles, sleep(2) will add ~170 minutes to the script's runtime 
            time.sleep(2)

            # read each document as one big string
            with open(os.path.join(root, fname), 'r') as page:
                #parse files
                content = parse_page(page)
                txt = text_prep(content)

                # print([os.path.join(root,fname)[39:75], txt[0:50], len(txt)])
                # df = df.append(pd.Series([os.path.join(root,fname)[39:75], len(txt), txt]), ignore_index=True)
            outfile.write(os.path.join(root,fname)[39:75] + '|' + str(len(txt)) + '|' + txt + "\n")

# df.columns = ['KAS_Name', 'textlength', 'txt']
# df.to_csv(os.path.join(os.getcwd(), 'assetcrawl.csv'), sep='|')
# df.head()
#                 
stop = timeit.default_timer()
print('Time: ', stop-start)


#%%
import pandas as pd

df = pd.read_csv('assetcrawl.csv', sep='|', header=None, names=['KAS_Name', 'textlength', 'txt'])
df.head()

#%%
df['textlength'].describe()


#%%
df[df['textlength'] < 1000].sort_values(by=['textlength'])
# we do have files with 0 text - they're infographics

#%%
df[df['textlength'] >10000].sort_values(by=['textlength'])

#%%
