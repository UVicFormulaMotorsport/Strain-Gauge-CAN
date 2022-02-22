from Phidget22.Phidget import *
from Phidget22.Devices.VoltageRatioInput import *
import struct

#converts floats to to IEEE 754 binary represenation in 32 bits
def binary(num):
    return ''.join('{:0>8b}'.format(c) for c in struct.pack('!f',num))


def main():
    Serial1 = 111111 #input first phidget serial number here
    Serial2 = 100000 #input second phidget serial number here
    WaitValue = 5000 #corresponds to how long a channel remains open and unattached before timing out
    Gain = 128 #Phidget gain value for microstrain calculation
    GF = 2 #gauge factor
    nu = 0.3 #Poisson ratio for steel
   


    #Creating an array of channels

    SG = [VoltageRatioInput() for i in range (0, 6)]

    #populating channel parameters
    for i in range (0, 6):
        if i < 4:
            SG[i].setDeviceSerialNumber(Serial1)
            SG[i].setChannel(i)
        else:
            SG[i].setDeviceSerialNumber(Serial2)
            SG[i].setChannel(i-4) 
        SG[i].openWaitForAttachment(WaitValue)

    #enabling each bridge and setting the gain
    for i in range (0, 6):
        SG[i].setBridgeEnabled(True)
        SG[i].setBridgeGain(BridgeGain.Bridge_Gain_128) #Possible values of Bridge_Gain_X where x = 1, 8, 16, 32, 64, or 128
    #Connect to CAN bus
    can0 = can.interface.Bus(Channel = 'can0', bustype = 'socketcan_ctypes')#This needs to be confirmed

    VRatio = [0 for i in range (0,6)] #creating array to store raw ratios
    MicroStrains = [0 for i in range (0,6)] #creating list to store readings converted to microstrains
    Bin32MicroStrains = [0 for i in range (0,6)] #Creating list to store binary reps. of strain in IEEE 754 32-bit
 
    #creating a list of size 1 byte arrays to hold separated binary float representation
    SGOutputA = [bytes(1) for i in range (0,6)]
    SGOutputB = [bytes(1) for i in range (0,6)]
    SGOutputC = [bytes(1) for i in range (0,6)]
    SGOutputD = [bytes(1) for i in range (0,6)]



    #loop for data collection (should constantly feed data)
    while(1):

    
        #get voltage ratio for each gauge (6 gauges),convert to microstrains, 
        # and convert microstrains to IEEE 32-bit binary representation of float value 
        for i in range (0,6):
            VRatio[i] = SG[i].getVoltageRatio()
            MicroStrains[i] = -2000000*VRatio[i]/(Gain*GF*((nu+1)-VRatio[i]*(nu-1)))#convert to Micro strains. 
            Bin32MicroStrains[i] = binary(MicroStrains[i])

            #separating 32 bit float representation into 8 bit words
            SGOutputA[i] = Bin32MicroStrains[i][0:8]
            SGOutputB[i] = Bin32MicroStrains[i][8:16]
            SGOutputC[i] = Bin32MicroStrains[i][16:24]
            SGOutputD[i] = Bin32MicroStrains[i][24:]
        
        #Creating the messages. The arbitration_id needs to be updated with real address
        SG0and1Msg = can.Message(arbitration_id = 0x123, data = [SGOutputA[0], SGOutputB[0], SGOutputC[0], SGOutputD[0], SGOutputA[1], SGOutputB[1], SGOutputC[1], SGOutputD[1]], extended_id=False)
        SG2and3Msg = can.Message(0x123,[SGOutputA[2], SGOutputB[2], SGOutputC[2], SGOutputD[2], SGOutputA[3], SGOutputB[3], SGOutputC[3], SGOutputD[3]], extended_id=False)
        SG4and5Msg = can.Message(0x123,[SGOutputA[4], SGOutputB[4], SGOutputC[4], SGOutputD[4], SGOutputA[5], SGOutputB[5], SGOutputC[5], SGOutputD[5]], extended_id=False)
        
        #Sending the Messages
        can0.send(SG0and1Msg)
        can0.send(SG2and3Msg)
        can0.send(SG4and5Msg)

        
    
    #Closing channels. Probably not necessary
    for i in range (0, 8):
        SG[i].close()

main()

