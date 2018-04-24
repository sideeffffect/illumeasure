#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Illuminance measurement
"""

import os
import sys
import ftdi1 as ftdi
import time


def bcc(i):
  bytes = map(ord, i)
  res = reduce(lambda x, y: x ^ y, bytes)
  return "%02x" % res

def encodeShort(receptorHead, command, parameter):
  bccable = receptorHead + command + parameter + "\x03" # 0x03 for ETX
  bccResult = bcc(bccable)
  return "\x02" + bccable + bccResult + "\x0D\x0A" # \x02 for STX, \x0D for CR, \x0A for LF

def dataToNumber(i):
  if i == "      ":
    return None
  else:
    v = int(i[1:5])
    e = int(i[5]) - 4
    r = v * (10**e)
    return -r if i[0] == '-' else r

def decodeLong(i):
  expectedBcc = bcc(i[1:28])
  actualBcc = i[28:30]
  if int(actualBcc, 16) != int(expectedBcc, 16):
    raise ValueError("BCC check failed, expected BCC '%s', got '%s', received '%s'." % (expectedBcc, actualBcc, i))
  
  receptorHead = i[1:3]
  command = i[3:5]
  status = i[5:9]
  data1 = dataToNumber(i[9:15])
  data2 = dataToNumber(i[15:21])
  data3 = dataToNumber(i[21:27])
  
  return (receptorHead, command, status, (data1, data2, data3))

shortLength = 14
longLength = 32

pcConnectionMode = encodeShort("00", "54", "1   ")
pcConnectionModeResponse = encodeShort("00", "54", "    ")

setMeasurementConditions01 = encodeShort("01", "10", "0200")
#setMeasurementConditions01Response = encodeShort("01", "10", "   0")

def main():

  # version
  print ('version: %s\n' % ftdi.__version__)

  # initialize
  ftdic = ftdi.new()
  if ftdic == 0:
      print('new failed: %d' % ret)
      os._exit(1)


  ret, devlist = ftdi.usb_find_all(ftdic, 0x0403, 0x6001)

  if ret < 0:
      print('ftdi_usb_find_all failed: %d (%s)' %
            (ret, ftdi.get_error_string(ftdic)))
      os._exit(1)
  print('devices: %d' % ret)
  curnode = devlist
  i = 0
  while(curnode != None):
      ret, manufacturer, description, serial = ftdi.usb_get_strings(
          ftdic, curnode.dev)
      if ret < 0:
          print('ftdi_usb_get_strings failed: %d (%s)' %
                (ret, ftdi.get_error_string(ftdic)))
          os._exit(1)
      print('#%d: manufacturer="%s" description="%s" serial="%s"\n' %
            (i, manufacturer, description, serial))
      curnode = curnode.next
      i += 1

  # open usb
  ret = ftdi.usb_open(ftdic, 0x0403, 0x6001)
  if ret < 0:
      print('unable to open ftdi device: %d (%s)' %
            (ret, ftdi.get_error_string(ftdic)))
      os._exit(1)




  ret = ftdi.setflowctrl(ftdic, ftdi.SIO_XON_XOFF_HS)
  if ret < 0:
      print('ftdi_set_bitmode failed: %d (%s)' %
            (ret, ftdi.get_error_string(ftdic)))
      os._exit(1)

  ret = ftdi.set_bitmode(ftdic, 0xff, ftdi.BITMODE_RESET)
  if ret < 0:
      print('ftdi_set_bitmode failed: %d (%s)' %
            (ret, ftdi.get_error_string(ftdic)))
      os._exit(1)

  ret = ftdi.set_baudrate(ftdic, 9600)
  if ret < 0:
      print('ftdi_set_baudrate failed: %d (%s)' %
            (ret, ftdi.get_error_string(ftdic)))
      os._exit(1)

  ret = ftdi.set_line_property(ftdic, ftdi.BITS_7, ftdi.STOP_BIT_1, ftdi.EVEN)
  if ret < 0:
      print('ftdi_set_line_property failed: %d (%s)' %
            (ret, ftdi.get_error_string(ftdic)))
      os._exit(1)


  ret = ftdi.write_data(ftdic, pcConnectionMode)
  if ret < 0:
      print('ftdi_write_data failed: %d (%s)' %
            (ret, ftdi.get_error_string(ftdic)))
      os._exit(1)
  else:
    print('ftdi_write_data wrote "%s", %d bytes' % (pcConnectionMode, ret))
  time.sleep(0.1)

  ret, response = ftdi.read_data(ftdic, shortLength)
  if ret < 0:
      print('ftdi_read_data failed: %d (%s)' %
            (ret, ftdi.get_error_string(ftdic)))
      os._exit(1)
  else:
      print('ftdi_read_data read "%s", %d bytes' % (response, ret))
  
  if response == pcConnectionModeResponse:
    print("Successfully set to PC mode")
  else:
    print('wrong PcConnectionMode response, expected "%s", got "%s".' % (pcConnectionModeResponse, response))
    os._exit(1)
  time.sleep(0.5)


  ret = ftdi.write_data(ftdic, setMeasurementConditions01)
  if ret < 0:
      print('ftdi_write_data failed: %d (%s)' %
            (ret, ftdi.get_error_string(ftdic)))
      os._exit(1)
  else:
    print('ftdi_write_data wrote "%s", %d bytes' % (setMeasurementConditions01, ret))
  time.sleep(0.1)


  ret, response = ftdi.read_data(ftdic, longLength)
  if ret < 0:
      print('ftdi_read_data failed: %d (%s)' %
            (ret, ftdi.get_error_string(ftdic)))
      os._exit(1)
  else:
      print('ftdi_read_data read "%s", %d bytes' % (response, ret))

  decoded = decodeLong(response)

  print(decoded)


  # close usb
  ret = ftdi.usb_close(ftdic)
  if ret < 0:
      print('unable to close ftdi device: %d (%s)' %
            (ret, ftdi.get_error_string(ftdic)))
      os._exit(1)

  print ('device closed')
  ftdi.free(ftdic)

if __name__ == "__main__":
    main()

