import time
from typing import Protocol, Sequence, Optional
from datetime import datetime, timedelta


class Leg(Protocol):
    """Abstract description of Leg"""

    depUtc: datetime
    depLt: datetime
    arrUtc: datetime
    arrLt: datetime
    flightDesignator: str
    rotation: Optional[int]
    isTransport: bool = False
    day: int

class Duty(Protocol):
    """Abstract description of Duty"""

    legs: Sequence[Leg]

#1
def isEarly(duty: Duty) -> bool:
    """Check if a Duty started before 09:00 LT"""
    first_leg = duty.legs[0]  # Erstes Leg der Duty
    return first_leg.depLt.time() < time(9, 0)

#2
def isLate(duty: Duty) -> bool:
    """Check if a Duty started after 21:00 LT"""
    last_leg = duty.legs[-1]  # Letztes Leg der Duty
    return last_leg.depLt.time() >= time(21, 0)

#3
def reducedRest(duty1: Duty, duty2: Duty) -> bool:
    # Get the last arrival time of the first duty
    last_arrival_time = duty1.legs[-1].arrUtc
    
    # Get the first departure time of the second duty
    first_departure_time = duty2.legs[0].depUtc
    
    # Calculate the time gap between duties
    gap = first_departure_time - last_arrival_time
    
    # Check if the gap is less than 9 hours
    if gap < timedelta(hours=9):
        return True  # Reduced rest
    return False  # Sufficient rest

#alternative shorter
def reducedRest(duty1: Duty, duty2: Duty) -> bool:
    return (duty2.legs[0].depUtc - duty1.legs[-1].arrUtc) < timedelta(hours=9)

#4
def noEarlyAfterReducedRest(pairing: Sequence[Duty]) -> bool:
    for i in range(len(pairing) - 2):  # Check up to the penultimate duty
        duty1, duty2, duty3 = pairing[i], pairing[i + 1], pairing[i + 2]
        
        # Check if the sequence "duty - reduced rest - duty - early duty" is encountered
        if reducedRest(duty1, duty2) and isEarly(duty3):
            return False  # Invalid sequence
    
    return True  # Valid sequence

#5
def noEarlyAfterLate(duties: Sequence[Duty]) -> bool:
    """Check that no early duty follows a late duty"""
    late_duty_encountered = False

    for duty in duties:
        if isLate(duty):
            late_duty_encountered = True
        elif late_duty_encountered:
            if isEarly(duty):
                return True
            late_duty_encountered = False

    return False

#6
def hasMaxSectors(duty: Duty) -> bool:
    # Check if the duty has a maximum of 3 legs and one transport
    num_legs = len(duty.legs)
    num_transports = sum(1 for leg in duty.legs if leg.isTransport)
    
    return num_legs <= 3 and num_transports == 1

def maxSectors(pairing: Sequence[Duty]) -> bool:
    reduced_rest = False  # Flag to track if the previous rest was reduced
    
    for i in range(len(pairing) - 2):  # Check up to the penultimate duty
        duty1, duty2, duty3 = pairing[i], pairing[i + 1], pairing[i + 2]
        
        # Check if the rest between duties is reduced
        if reducedRest(duty1, duty2):
            reduced_rest = True
        else:
            reduced_rest = False
        
        # Check if the duty after reduced rest has max 3 legs and one transport
        if reduced_rest and not hasMaxSectors(duty3):
            return False  # Invalid sequence
    
    return True  # Valid sequence

#7
def cico(leg: Leg):
    # Calculate check-in time (1 hour before the leg starts)
    check_in_time = leg.depLt - timedelta(hours=1)

    # Calculate check-out time (30 minutes after landing)
    check_out_time = leg.arrLt + timedelta(minutes=30)

    return check_in_time, check_out_time

#8
def minSittime(pairing: Sequence[Duty]) -> bool:
    for i in range(len(pairing) - 1):
        current_duty = pairing[i]
        next_duty = pairing[i + 1]

        # Check if the first leg of the current duty is a transport leg
        if current_duty.legs[0].isTransport:
            # Calculate the time between the last leg of the current duty and the first leg of the next duty
            last_leg_current_duty = current_duty.legs[-1]
            first_leg_next_duty = next_duty.legs[0]
            time_between_legs = first_leg_next_duty.depLt - last_leg_current_duty.arrLt

            # Check if the time between legs is less than 1 hour and 40 minutes
            if time_between_legs < timedelta(hours=1, minutes=40):
                return False

    return True


#9
def restTime(duty: Duty) -> bool:
    prev_leg = None  # Initialize the previous leg as None
    for leg in duty.legs:
        if prev_leg is not None and leg.flightDesignator != prev_leg.flightDesignator:
            # Aircraft change detected
            time_gap = (leg.depUtc - prev_leg.arrUtc).total_seconds() / 60  # Calculate time gap in minutes
            if time_gap < 50:
                return False  # Insufficient rest time
        prev_leg = leg  # Update the previous leg
    return True  # Sufficient rest time

#10
def maxEarlyDuties(duties: Sequence[Duty]) -> bool:
    early_shift_count = 0  # Zähler für aufeinander folgende Frühschichten

    for duty in duties:
        if isEarly(duty):
            early_shift_count += 1
            if early_shift_count > 3:
                return False
        else:
            early_shift_count = 0

    return True


#11 duty limit not max actitivty
def maxDuty(pairing: Sequence[Duty]) -> bool:
    return len(pairing) <= 4

#12
def maxPairingLength(duties: Sequence[Duty]) -> bool:
    if not duties:
        return False

    first_leg = duties[0].legs[0]
    last_leg = duties[-1].legs[-1]

    total_duration = last_leg.arrUtc - first_leg.depUtc

    return total_duration.days <= 4

#13
def maxTransports(pairing: Sequence[Duty]) -> bool:
    transport_count = 0
    for duty in pairing:
        for leg in duty.legs:
            if leg.isTransport:
                transport_count += 1
                if transport_count > 10:
                    return False  # Exceeds the maximum number of transports (10)
    return True  # Does not exceed the maximum number of transports (10)

#14
def maxAircraftChanges(pairing: Sequence[Duty]) -> bool:
    aircraft_change_count = 0
    for duty in pairing:
        prev_aircraft = None  # Initialize the previous aircraft as None
        for leg in duty.legs:
            if prev_aircraft is not None and leg.flightDesignator != prev_aircraft:
                # Aircraft change detected
                aircraft_change_count += 1
                if aircraft_change_count > 2:
                    return False  # Exceeds the maximum number of aircraft changes (2)
            prev_aircraft = leg.flightDesignator  # Update the previous aircraft
    return True  # Pairing is legal in terms of aircraft changes (within 2)

#15
def maxDutyDays(duty: Duty) -> bool:
    # Calculate the duration between the first and last legs
    first_leg_dep = duty.legs[0].depUtc
    last_leg_arr = duty.legs[-1].arrUtc
    duration = last_leg_arr - first_leg_dep
    
    # Check if the duration exceeds 2 days
    if duration > timedelta(days=2):
        return False  # Duty spans over more than 2 days
    return True  # Duty is within 2 days
