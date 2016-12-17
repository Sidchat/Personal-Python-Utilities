#!/usr/bin/python
#!/usr/bin/python
# PURPOSE: This script sounds alarm after sleeping number of seconds derived from user input
# CHANGE CONTROL:
# Sid Chatterjee     11/24/2016     Draft

from __future__ import with_statement, nested_scopes, generators, division, absolute_import, print_function,unicode_literals
import time, sys
from pygame import mixer

def alertme(sleeptime, NumOfAlarms):
    """The function **alertme** performs *sleeps number of seconds as supplied via sleeptime variable*
    TESTING:
    >>> alertme(30)
    Going to wait for 30 seconds.
    Alarm time!! Ten alarms to start.
    Press Control+C to stop the alarm.
    """
    print('Current time is {}'.format(time.ctime()))
    print("Going to wait for "+str(sleeptime)+' seconds.')
    try:
        time.sleep(sleeptime)
    except KeyboardInterrupt:
        print ('Thank you! Alarm is cancelled now.')
        return
    mixer.init()
    mixer.music.load('/home/sid/PycharmProjects/Utilities/244932__kwahmah-02__short-buzzer.wav')
    print('Alarm time!! Ten alarms to start.')
    print('Press Control+C to stop the alarm.')
    try:
        for r in range(NumOfAlarms):
            time.sleep(1)
            mixer.music.play()

    except KeyboardInterrupt:
        print('Alarm stopped. Thank you.')


def calc_seconds(num, qualifier):
    """This function **calc_seconds** calculates *number of seconds based on arguments provided and return it*
    TESTING:
    >>>calc_seconds(1,'HR')
    3600
    """
    print('Supplied values are {}, {}'.format(str(num), qualifier))
    qualifier_multiplier={'SEC':1, 'SECONDS':1,'MIN':60, 'HR':3600, 'HOUR':3600, 'HOURS':3600, 'MINS':60, 'DAY':1440, 'DAYS':1440,'MON':43200, 'MONTH':43200, 'MONTHS':43200, 'YEAR':518400}
    return qualifier_multiplier.get(qualifier,0) * num


if __name__ == '__main__':
    if len(sys.argv) <> 3:
        print('You need to supply two arguments, 1st for number of time units and 2nd for time unit. Try again.')
        sys.exit(1)

    alertme(calc_seconds(int(sys.argv[1]),str(sys.argv[2]).upper()),10)
