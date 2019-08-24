# AcousticRecord

>A model is not a load of mathematics, as some people think; nor is it some unrealizable ideal, as others believe. It is simply an account expressed as you will – of *the actual organization of a real system.* Without a model of the system to be regulated, you cannot have a regulator.
>
>— Stafford Beer, [Designing Freedom 1973](http://ada.evergreen.edu/~arunc/texts/cybernetics/beer/book.pdf), pg. 11

<br>

This repository contains a very simple Python class. It allows users to simulate observation of an acoustic environment; what we might call an 'audio recording' or simply a 'record'. Specifically, it simulates time series that conform to [National Park Service measurement standards](https://www.nps.gov/subjects/sound/upload/NSNSDTrainingManual_AcousticalAmbientMonitoring-508.pdf): one-second averages of broadband sound level *Leq, 1s (12.5Hz - 20kHz)*. <br>

Within the ecological paradigm of acoustics, the system we're describing (the acoustic environment) has two separate components: **natural sound** and **noise**. However, due to the superposition of sound, both signals are observed at the microphone together. Therefore it is of great interest to have the means to control each component indepenantly. Especially so if we can describe effects on observed metrics once the signals have been superposed.<br>

The main assumption of the model? **Noise is created by an ideal acoustic point source.** That's it. Most other attributes of the system can be user defined (within reason.) The observed phenomena then follow from physical principle.<br>

----

## Downloading and using this module

Use [git](https://git-scm.com/) to clone the repository.  Using the path to the repository on your local disk, import the `AcousticRecord` class: 

```
import sys
sys.path.append(r"\*\*\stringtranscribe")

from AcousticRecord import AcousticRecord
```

<a rel="license" href="http://creativecommons.org/licenses/by/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by/4.0/88x31.png" /></a><br />This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International License</a>.

Work with this module is [highly enhanced through the use of `soundDB`](https://github.com/gjoseph92/soundDB) to load empirical observations.

----

## The `AcousticRecord` class

We begin using the module by initializing a record. 

For now, records are assumed to have:

- a length, in days
- a certain number of vehicles moving past the mic location (*regardless of whether they are audible or not*)

Here's how you would initialize a 28 day record with 2000 aircraft moving past the mic:
```
rec = AcousticRecord(28, 2000)
```
At this point the object has no time series associated with it, but it does have some attributes which can be useful for setting up other variables.

```
# the length of the record in seconds
rec.duration 

# the number of days we just entered
rec.n_days 

# the number of events we just entered
rec.n_events 
```
In addition, some traffic properties have been initialized using default values. These all can be (and for most useful purposes, *should* be) reassigned by the user!
```
# a numpy array representing the maximum Leq, 1s for each of our 2000 aircraft overflights 
rec.Lmax_distribution 

# a numpy array representing the 'full-width at half maximum' duration of each overflight, in seconds
rec.fwhm_duration_distribution

# a numpy array representing the time at which Lmax occurs for each overflight, in seconds elapsed
rec.center_times
```
A trivial example would be resetting all the durations to a constant value, 100 seconds:
```
rec.fwhm_duration_distribution = np.full(shape=rec.n_events, fill_value=100)
```

---

**Noise has *no physical meaning* outside of the natural ambient acoustic energy it is embedded in.** So our next task is to add some ambience to our record. It can be done in several ways.
<br>
It's convenient to use a constant, scalar value:
```
rec.add_ambience(25.6)
```
Some environments are more appropriately simulated using a time series:
```
# remember A sin(Bx) + D, where A is the amplitude, B/2pi is the period, and D is the vertical offset
B = (2*np.pi)/(12*3600) # a 12 hour wavelength

nocturnal_increase = 5*np.sin(B*np.arange(rec.duration))+25.6
rec.add_ambience(nocturnal_increase)
```
Seasonal changes could also be simulated in this way. <br>

---

Once ambience has been added we have access to three time series: 
```
# the natural ambience we just defined
rec.ambient 

# one aggregate, superposed time series of all noise events
rec.event_record

# furthermore... the superposition of noise onto the ambient
# this is what a microphone would provide
rec.full_record
```
We also have access to the *observed* bounds of noise and quiet. These are based off the intervals of time where noise was greater in amplitude than the ambient.
```
# start and end times of noise
rec.noise_intervals

# start and end times of quiet
rec.noise_free_intervals

# for example, these are all the times a noise:
rec.T[0]
