#coding=utf-8

import hiai
from hiai.nn_tensor_lib import DataType
import imageNetClasses
import jpegHandler
import os
import numpy as np
import time

resnet18OmFileName='./models/Resnet18.om'
srcFileDir = './ImageNetRaw/'
dstFileDir = './resnet18Result/'

def CreateGraph(model,modelInWidth,modelInHeight,dvppInWidth,dvppInHeight):

	#����get_default_graph��ȡĬ��Graph���ٽ������̱���
	myGraph = hiai.hiai._global_default_graph_stack.get_default_graph()
	if myGraph is None :
		print 'get defaule graph failed'
		return None
	print 'dvppwidth %d, dvppheight %d'%(dvppInWidth,dvppInHeight)
	# ���̱���	
	cropConfig = hiai.CropConfig(0,0,dvppInWidth,dvppInHeight)
	print 'cropConfig ', cropConfig 
	resizeConfig = hiai.ResizeConfig(modelInWidth,modelInHeight)
	print 'resizeConfig ', resizeConfig

	nntensorList=hiai.NNTensorList()
	print 'nntensorList', nntensorList	

	resultCrop = hiai.crop(nntensorList,cropConfig)
	print 'resultCrop', resultCrop

	resultResize = hiai.resize(resultCrop, resizeConfig)
	print 'resultResize', resultResize

	resultInference = hiai.inference(resultResize, model, None)
	print 'resultInference', resultInference

	if ( hiai.HiaiPythonStatust.HIAI_PYTHON_OK == myGraph.create_graph()):
		print 'create graph ok !!!!'
		return myGraph
	else :
		print 'create graph failed, please check Davinc log.'
		return None

def CreateGraphWithoutDVPP(model):

	#����get_default_graph��ȡĬ��Graph���ٽ������̱���
	print model
	myGraph = hiai.hiai._global_default_graph_stack.get_default_graph()
	print myGraph
	if myGraph is None :
		print 'get defaule graph failed'
		return None


	nntensorList=hiai.NNTensorList()
	print nntensorList

	# ������DVPP ����ͼƬ��ʹ��opencv ����ͼƬ
	resultInference = hiai.inference(nntensorList, model, None)
	print nntensorList
	print hiai.HiaiPythonStatust.HIAI_PYTHON_OK
	#print myGraph.create_graph()

	if ( hiai.HiaiPythonStatust.HIAI_PYTHON_OK == myGraph.create_graph()):
		print 'create graph ok !!!!'
		return myGraph
	else :
		print 'create graph failed, please check Davinc log.'
		return None


def GraphInference(graphHandle,inputTensorList):
	if not isinstance(graphHandle,hiai.Graph) :
		print "graphHandle is not Graph object"
		return None

	resultList = graphHandle.proc(inputTensorList)
	return resultList

def Resnet18PostProcess(resultList, srcFilePath, dstFilePath, fileName):

	if resultList is not None :
		# resultList ��һ��list����ÿ��item Ҳ��һ�� array�����list
		resultArray = resultList[0]

		batchNum = resultArray.shape[0]
		confidenceNum = resultArray.shape[3]
		confidenceList = resultArray[0,0,0,:]

		confidenceArray = np.array(confidenceList)
		confidenceIndex = np.argsort(-confidenceArray)

		firstClass = confidenceIndex[0]
		firstConfidence = confidenceArray[firstClass]
		firstLabel = imageNetClasses.imageNet_classes[firstClass]
		print fileName + '    ' + '%.2f%%' % (firstConfidence*100) + '\t' + firstLabel


		dstFileName = os.path.join('%s%s' % (dstFilePath, fileName))
		srcFileName = os.path.join('%s%s' % (srcFilePath, fileName))

		jpegHandler.putText(srcFileName, dstFileName, '%.2f%%' % (firstConfidence*100) + ':' + firstLabel)

		'''
		# ��һ����ȡ�������ķ�ʽ����result_list ת����NNTensorList��Ȼ����ȡ��NNTensor�����ͨ��NNTensor��data_list��ȡ�����ݣ���������Ϊnumpy.array
		result_nntensor_list=hiai.NNTensorList(resultList)
		result_nn_tensor = result_nntensor_list[0]
		res_array = result_nn_tensor.data_list[0]
		'''

		return None
	else :
		print 'graph inference failed '
		return None

def main():
	inferenceModel = hiai.AIModelDescription('restnet18',resnet18OmFileName)
	print resnet18OmFileName
	print inferenceModel
	# we will resize the jpeg to 256*224 to meet resnet18 requirement vis opencv,
	# so DVPP resizing is not needed  	
	myGraph = CreateGraphWithoutDVPP(inferenceModel)
	if myGraph is None :
		print "CreateGraph failed"
		return None

	# in this sample demo, the resnet18 model requires 256*224 images
	dvppInWidth = 256
	dvppInHeight = 224
	
	'''
	# in this sample demo, the resnet18 model requires 256*224 images
	modelInWidth=256	
	modelInHeight=224

	dvppInWidth = 400
	dvppInHeight = 300

	# the input image should be 512*448 , DVPP will resize it to 256*224 to meet the resnet18 requirement.
	myGraph = CreateGraph(inferenceModel, modelInWidth, modelInHeight, dvppInWidth, dvppInHeight)
	if myGraph is None :
		print "CreateGraph failed"
		return None
	'''
	start = time.time()

	pathDir =  os.listdir(srcFileDir)
	for allDir in pathDir :
		child = os.path.join('%s%s' % (srcFileDir, allDir))
		if( not jpegHandler.is_img(child) ):
			print '[info] file : ' + child + ' is not image !'
			continue 

		# read the jpeg file and resize it to required w&h, than change it to YUV format.	
		input_image = jpegHandler.jpeg2yuv(child, dvppInWidth, dvppInHeight)

		inputImageTensor = hiai.NNTensor(input_image,dvppInWidth,dvppInHeight,3,'testImage',DataType.UINT8_T, dvppInWidth*dvppInHeight*3/2) 
		nntensorList=hiai.NNTensorList(inputImageTensor)

		resultList = GraphInference(myGraph,nntensorList)
		if resultList is None :
			print "graph inference failed"
			continue

		Resnet18PostProcess(resultList, srcFileDir, dstFileDir, allDir)

	end = time.time()
	print 'cost time ' + str((end-start)*1000) + 'ms'		
	

	hiai.hiai._global_default_graph_stack.get_default_graph().destroy()



	print '-------------------end'


if __name__ == "__main__":
	main()