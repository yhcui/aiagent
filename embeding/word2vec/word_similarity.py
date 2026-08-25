from gensim.models import word2vec
import multiprocessing

segment_folder =  './journey_to_the_west/segment'
sentences = word2vec.PathLineSentences(segment_folder)
model = word2vec.Word2Vec(sentences, vector_size=100, window=3, min_count=1)

print(model.wv['孙悟空'])
print(model.wv.similarity('孙悟空', '猪八戒'))
print(model.wv.most_similar(positive=['孙悟空', '唐僧'], negative=['孙行者']))

# 设置模型参数，进行训练
model2 = word2vec.Word2Vec(sentences, vector_size=128, window=5, min_count=5, workers=multiprocessing.cpu_count())
# 保存模型
model2.save('./models/word2Vec.model')