#!/usr/bin/python
from optparse import OptionParser
import sys
import re
import json
import types
import math
import os

import pandas as pd
import numpy as np



def main():

    global opts
    usage= "--help"
    metricNameStr='metricName'
    metricValueStr='metricValue'
    global nIter
    g_opStr = 'operation'

    parser = OptionParser(usage=usage)
    homeStr=os.environ['HOME']


    parser.add_option("-i", "--inputDir", type="string",
                      action="store", dest="inputDirectory", default= os.path.join(homeStr, "summaryResults/profileResult") ,
                      help="input directory ")
   
    parser.add_option("-o", "--outputDir", type="string",
                      action="store", dest="gpuwattch_xml_outputFiles", default= os.path.join(homeStr, "summaryResults/summaryofMetrics"),
                      help="output directory ")
    parser.add_option("-e", "--exe_run",
                      action="store_false", dest="readExeTimeFromRunResult", default=True,
                      help="readExeTimeFromRunResult")
    parser.add_option("-a", "--energy_outs", type="string",
                      action="store", dest="energy_outputFiles", default=os.path.join(homeStr, "summaryResults/energy_outputFiles"),
                      help="enery output file ")

    (opts, args) = parser.parse_args()
#    nIter=opts.nIter
    readExeTimeFromRunResult = opts.readExeTimeFromRunResult

    (opts, args) = parser.parse_args()
    os.makedirs(opts.gpuwattch_xml_outputFiles, exist_ok=True)
    allInOneFile = os.path.join(opts.energy_outputFiles, "allMetricsInOneFile.csv")
    dataFramContainingAllStats=pd.DataFrame()
    for operationName in sorted(os.listdir(opts.inputDirectory)):
        subDirName=os.path.join(opts.inputDirectory, operationName)
        outputFileName=os.path.join(opts.gpuwattch_xml_outputFiles,operationName+".csv")
        print(operationName)
        summaryDataFrame = pd.DataFrame(columns=[metricNameStr, metricValueStr])
        scalForExce = 1
        infile = open(os.path.join(opts.inputDirectory, operationName, 'executionTimeRunResult.tmp'))
        for tc, line in enumerate(infile):
            if (tc == 0):
                print("nIter=" + line)
                nIter = eval(line.strip())  # warmup
                summaryDataFrame = summaryDataFrame.append(
                    {metricNameStr: 'nIter', metricValueStr: nIter},
                    ignore_index=True)
            if (tc == 1):
                print("runtime=" + line)
                tmpExeTime = eval(line.strip()) * 1.0e-3
        for metricFileName in  sorted(os.listdir(subDirName)):
            print(metricFileName)
            if metricFileName[0]!='.' and metricFileName[-4:]!='.tmp' :
                metricName=metricFileName[:-4]
                pathToMetricFileNames = os.path.join(opts.inputDirectory, operationName, metricFileName)
                print(pathToMetricFileNames+"\n")
                if (metricName!='powerConsumption'):
                    print(pathToMetricFileNames)
                    dataFrame = pd.read_csv(pathToMetricFileNames, comment='=')
                else:
                    tmpLines = open(pathToMetricFileNames, 'rt')
                    for line in tmpLines:
                        if "System profiling result" in line.strip():
                            break
                    open("pathToMetricFileNames" + "_tmp", 'wt').writelines(tmpLines)
                    dataFrame = pd.read_csv("pathToMetricFileNames" + "_tmp", comment='=')

                metricValue=0
                print(metricName)

                percentage = False
                if ((type(dataFrame.iloc[0].loc['Avg']) == str) and (dataFrame.iloc[0].loc['Avg'][-1] == '%')):
                    percentage = True
                    dataFrame['Avg'] = dataFrame['Avg'].str.rstrip('%').astype('float')
                for i in range(len(dataFrame)):



                    if(percentage==True):

                        metricValue+=dataFrame.iloc[i].loc['Avg']
                    elif (metricName == 'executionTime'):

                        if(readExeTimeFromRunResult!=True):

                            if(i==0 and type(dataFrame.iloc[i].loc['Avg'])==str and (dataFrame.iloc[i].loc['Avg']=='ms')):
                                scalForExce=1.0e-3
                            if((i>0) and ('GPU activities' in dataFrame.iloc[i].loc['Type']) and ('CUDA memcpy' not in dataFrame.iloc[i].loc['Name']) ):
                                    metricValue +=float(dataFrame.iloc[i].loc['Avg'])* dataFrame.iloc[i].loc['Calls']*scalForExce
                                    print(dataFrame.iloc[i].loc['Avg']+"\n")
                    elif (metricName=='powerConsumption'):

                        tmpMax=0
                        for j in range(len(dataFrame)):
                            if ((j%4 ==3 ) and dataFrame.iloc[j].loc['Max']>tmpMax):
                                tmpMax=dataFrame.iloc[j].loc['Max']

                        metricValue=tmpMax

                    elif(type(dataFrame.iloc[i].loc['Avg']) != str and ('__uninitialized_fill') not in dataFrame.iloc[i].loc['Kernel'] and ('thrust::identity' not  in dataFrame.iloc[i].loc['Kernel'] )):
                        metricValue +=(dataFrame.iloc[i].loc['Avg']) * dataFrame.iloc[i].loc['Invocations']
                if (metricName == 'executionTime' ):
                    if(readExeTimeFromRunResult==False):
                        metricValue=metricValue/nIter
                    else:
                        metricValue=tmpExeTime


                if (percentage==True):
                    metricValue=metricValue/len(dataFrame)
                summaryDataFrame=summaryDataFrame.append({metricNameStr:metricName, metricValueStr:metricValue,g_opStr:operationName},ignore_index=True)

        print(summaryDataFrame)

        summaryDataFrame.to_csv(outputFileName)
        dataFramContainingAllStats = dataFramContainingAllStats.append(summaryDataFrame)
            #if not dataFrame.empty:
                #print(dataFrame)

    dataFramContainingAllStats.to_csv(allInOneFile)
if __name__ == '__main__':
    main()
