#!/usr/bin/env python

#
#      Copyright (C) 2015 Jozef Hutting <jehutting@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import sys
import os
import subprocess
import logging
import threading
import time
import RPi.GPIO as GPIO

__author__ = 'Jozef Hutting'
__copyright__ = 'Copyright (C) 2015 Jozef Hutting <jehutting@gmail.com>'
__license__ = 'GPLv2'
__version__ = '0.12'

# the REAL OMXPlayer
OMXPLAYER = 'omxplayer'
# REAL OMXPLAYER options
OMXPLAYER_ARGS = [
     #'--display=4',  # Raspberry Pi touchscreen
     '--no-osd', # Do not display status information on screen
     '--loop' # Loop file.
    ]

omxplayer = None


class OMXPlayer:

    '''
    Note: this python wrapper to control OMXPlayer is a very simple implementation.
    If you want a more (on the edge) control over OMXPlayer, I suggest to use 
    Will Price OMXPlayer wrapper (https://github.com/willprice/python-omxplayer-wrapper).
    '''

    process = None
    running = False
    completed = False

    def __init__(self):
        self.logger = logging.getLogger('__OMXPlayer__')

    def log(self, args):
        self.logger.debug('{0}'.format(args))

    def log_error(self, args):
        self.logger.error('{0}'.format(args))

    def play(self, filename):

        def run_in_thread():

            #def monitor(process):
            #    process.wait()

            command = [OMXPLAYER]
            command.extend(OMXPLAYER_ARGS)  # default arguments
            command.append(filename)
            self.log('Full command={0}'.format(command))
            with open(os.devnull, 'w') as devnull:
                self.process = subprocess.Popen(command,
                                                stdin=subprocess.PIPE,
                                                stdout=devnull,
                                                stderr=devnull)

            # wait for REAL OMXPlayer process is running
            while self.process.poll() is not None:
                time.sleep(0.01) # seconds
                self.log('#')
            self.log('process PID={0}'.format(self.process.pid))
            self.running = True

            while True:
                if self.process.poll() is not None:
                    break
            self.log('REAL OMXPlayer exit status/return code : {0}'
                     .format(self.process.returncode))
            self.completed = True
            return

        if not os.path.isfile(filename):
             self.log_error('Error: File "{0}" not found!'.format(filename))
             raise IOError(filename)

        self.thread = threading.Thread(target=run_in_thread, args=())
        self.thread.start()
        self.log('Waiting for running REAL OMXPlayer...') 
        while(not self.running):
            continue;
        self.log('REAL OMXPlayer is up and running!') 

    def quit(self):
        p = self.process
        if (p is not None):
            try:
                self.log('Quitting REAL OMXPlayer...')
                self.running = False
                self.__key(b'q')  # send quit command           
                # wait for process termination 
                self.thread.join() 
            except:
                self.log_error('Error upon quitting REAL OMXPlayer: {0}'
                               .format(sys.exc_info()[0]))

    def pause(self):
        if self.running:
            self.log('Pause REAL OMXPlayer')
            self.__key(b' ') # SPACE character to pause

    def resume(self):
        if self.running:
            self.log('Resume REAL OMXPlayer')
            self.__key(b' ') # SPACE character to unpause

    def __key(self, value):
        if self.running:
            try:
                self.process.stdin.write(value)
                self.log("Key b'{0}' sent successfully".format(value))
            except:
                self.log_error('Error on sending key to REAL OMXPlayer: {0}'
                               .format(sys.exc_info()[0]))


class PirControl():

    '''
    PIR (motion) sensor input signal :
    - value 0 : no motion detected
    - value 1 : motion detected
    '''

    def __init__(self):
        self.logger = logging.getLogger('__PirControl__')
        # ------ H A R D W A R E configuration --------------------------------- 
        #self.gpio = 22  # BCM port number!
        #GPIO.setup(self.gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.gpio = 7  # BCM port number!
        GPIO.setup(self.gpio, GPIO.IN)
        # ----------------------------------------------------------------------
        self.state = self.__get_state()
        self.log('initial state={0}'.format(self.state))

    def __get_state(self):
        return GPIO.input(self.gpio)

    def start(self):
        self.log('start')
        GPIO.add_event_detect(self.gpio, GPIO.BOTH, callback=self.edge_callback
                              )#, bouncetime=1)
        self.state = self.__get_state()
        self.log('initial state={0}'.format(self.state))

    def log(self, args):
        self.logger.debug('{0}'.format(args))

    def edge_callback(self, channel):
        global omplayer
        state = self.__get_state()
        self.log('Edge detected {0}=>{1}'.format(self.state, state))
        # Hmmm...sometimes I get 0=0 and 1=>1 edges!?
        # I ONLY want the real edges!
        if state != self.state:
            if state == 1: # edge 0=>1
                self.log('Motion detected!')
                omxplayer.resume()
            else: # edge 1=>0
                self.log('NO motion detected')
                omxplayer.pause();
            self.state = state

    def motion_detected(self):
        self.state = self.__get_state()
        return self.state == 1


class Main():

    def __init__(self):
        self.logger = logging.getLogger('__Main__')

    def log(self, args):
        self.logger.debug('{0}'.format(args))

    def log_error(self, args):
        self.logger.error('{0}'.format(args))

    def run(self, filename):
      global omxplayer

      GPIO.setmode(GPIO.BCM)
      GPIO.setwarnings(False)

      omxplayer = OMXPlayer()
      pir_control = PirControl()
      return_code = 0 # OK

      try:    

          self.log('Waiting for operator clearing the scene...');
          while(pir_control.motion_detected()):
              continue;
          self.log('Video player is armed!');

          # handle the PIR sensor signal edges
          pir_control.start()

          # OMXPlayer doesn't have the ability to start in a PAUSED state, and
          # a command to start the PLAYING.
          # Therefor start with a PLAYING OMXPlayer...
          self.log("Start REAL OMXPlayer");
          omxplayer.play(filename)
          # ...but as soon it is playing, PAUSEd it, as we want it to start
          # playing on motion detection.
          self.log("Pausing REAL OMXPlayer");
          omxplayer.pause()

          # Wait here until OMXPlayer is done playing the file
          # Note: when the default arguments OMXPLAYER_ARGS contains '--loop'
          # the looping is stopped (aborted) by CTRL+C (KeyboardInterrupt event).
          self.log("Waiting for REAL OMXPlayer played the file...");
          while(not omxplayer.completed):
               continue            

      except IOError as e:
          self.log_error('Error: File "{0}" not found!'.format(e.message))
          return_code = -1

      except KeyboardInterrupt:
          """http://stackoverflow.com/questions/19807134/python-sub-process-ctrlc"""
          self.log('KeyboardInterrupt')
          omxplayer.quit()

      print('EXIT')
      GPIO.cleanup()
      return return_code


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)

    #filename = sys.argv[1]
    filename = '/mnt/video.mp4'

    if not os.path.isfile(filename):
        print('Error: File "{0}" not found!'.format(filename))
        sys.exit(-1)

    try:
        mainloop = Main();
        return_code = mainloop.run(filename);
    finally:
        pass
 
    sys.exit(return_code);
