import jieba
import os
import glob  # 引入标准库 glob，用于文件查找
source_folder = './journey_to_the_west/source'
segment_folder = './journey_to_the_west/segment'
def segment_lines(file_list, segment_out_dir,stopwords=[]):
    for i,file in enumerate(file_list):
        segment_out_name = os.path.join(segment_out_dir, 'segment_{}.txt'.format(i))
        with open(file,'rb') as f:
            document = f.read()
            document_cut = jieba.cut(document)
            sentences_segment = []
            for word in document_cut:
                if word not in stopwords:
                    sentences_segment.append(word)
            result = ' '.join(sentences_segment)
            result = result.encode('utf-8')
            with open(segment_out_name,'wb') as f2:
                f2.write(result)

file_list = glob.glob(os.path.join(source_folder, '*.txt'))
segment_lines(file_list, segment_folder)