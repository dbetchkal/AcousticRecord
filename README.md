# AcousticRecord

>A model is not a load of mathematics, as some people think; nor is it some unrealizable ideal, as others believe. It is simply an account expressed as you will – of *the actual organization of a real system.* Without a model of the system to be regulated, you cannot have a regulator.
>
>— Stafford Beer, [Designing Freedom 1973](https://archive.org/details/DesigningFreedom_CBC_Lectures), pg. 11

<br>

This repository contains a very simple Python class. It allows users to simulate observation of an acoustic environment; what we might call an 'audio recording' or simply a 'record'. Specifically, it simulates time series that conform to [National Park Service measurement standards](https://www.nps.gov/subjects/sound/upload/NSNSDTrainingManual_AcousticalAmbientMonitoring-508.pdf): one-second averages of broadband sound level [ *Leq, 1s (12.5Hz - 20kHz)* ]. <br>

Within the ecological paradigm of acoustics, the system we're describing (the acoustic environment) has two separate components: **natural sound** and **noise**. These signals are necessarially superposed when they arrive at the microphone. Therefore it is of great interest to have the means to control each component indepenantly. Especially so if we can describe effects on observation of acoustic metrics once the signals have been superposed.<br>

The main assumption of the model? **Noise is created by an ideal acoustic point source.** That's it. Most other attributes of the system can be user defined (within reason.) The observed phenomena then follow from physical principle.<br>

----

## Downloading and using this module

Use [git](https://git-scm.com/) to clone the repository.  Using the path to the repository on your local disk, import the `AcousticRecord` class: 

```
import sys
sys.path.append(r"\*\*\AcousticRecord")

from AcousticRecord import AcousticRecord
```

`AcousticRecord` requires `numpy`. Work with the module is [highly enhanced through the use of `soundDB`](https://github.com/gjoseph92/soundDB) to load empirical observations.

<a rel="license" href="http://creativecommons.org/licenses/by/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by/4.0/88x31.png" /></a><br />This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International License</a>.


----

## The `AcousticRecord` class

### Initializing a record
We begin by initializing a record. Records must have:

- a length, in days
- a certain number of vehicles moving past the mic location (*regardless of whether they are audible or not*)

Here's how you would initialize a 28 day record with 2000 aircraft moving past the mic:
```
rec = AcousticRecord(28, 2000)
```
At this point the object has no associated time series. It does have attributes which can be useful for setting up a simulation:

The length of the record in seconds:
```
>>> rec.duration 
2419200
```

The number of days we just entered:
```
>>> rec.n_days 
28
```

The number of events we just entered:
```
>>> rec.n_events 
2000
```
Traffic properties have also been initialized using default values as follows.

A numpy array representing the maximum Leq, 1s for each of our 2000 aircraft overflights:
```
>>> rec.Lmax_distribution
array([64.8, 58.1, 73.5, ..., 46.7, 20.7, 59.8]) 
```

A numpy array representing the 'full-width at half maximum' duration of each overflight, in seconds:
```
>>> rec.fwhm_duration_distribution
array([ 78.15853618, 130.0608868 , 129.35119917, ..., 152.25337917,
       156.49251599, 130.17474321])
```

A numpy array representing the time at which Lmax occurs for each overflight, in seconds elapsed:
```
>>> rec.center_times
array([1939102,  425068, 2067604, ...,  474626, 1192696, 1974440])
```


These all can be (and for most useful purposes, *should* be) reassigned by the user! A trivial modification example: reset all the durations to a constant value, 100 seconds:
```
rec.fwhm_duration_distribution = np.full(shape=rec.n_events, fill_value=100)
```

---

### Natural Ambient Acoustic Energy

**Noise has *no physical meaning* outside of the natural ambient acoustic energy it is embedded in.** So we must add some ambience to our record. It can be done in several ways.
<br>

For quick sketches, you can use a constant, scalar value:
```
rec.add_ambience(25.6)
```
<img src="https://github.com/dbetchkal/AcousticRecord/blob/master/AcousticRecord_figure1.png" alt="figure1" class="inline"/>

However, it's often more realistic to simulate ambience as a temporal process. The following example simulates an acoustic environment where atmospheric refraction causes conditions to become more energetic in the early hours of the morning:
```
# remember A sin(Bx) + D, where A is the amplitude, B/2pi is the period, and D is the vertical offset
B = (2*np.pi)/(24*3600) # one oscillation takes 24 hours

nocturnal_increase = 5*np.sin(B*np.arange(rec.duration))+25.6
rec.add_ambience(nocturnal_increase)
```
<img src="https://github.com/dbetchkal/AcousticRecord/blob/master/AcousticRecord_figure2.png" alt="figure1" class="inline"/>

---
### An acoustic record: the superposition of natural ambience and noise

Once ambience has been added we have array access to three time series: 

The natural ambience we just defined...
```
>>> rec.ambient
array([25.6, 25.6, 25.6, ..., 25.6, 25.6, 25.6]) 
```

...a time series of noise, including overlap (if it occurs):
```
>>> rec.event_record
array([0., 0., 0., ..., 0., 0., 0.])
```
The superposition of noise and ambient accounting for masking. <br> Importantly **this approximates what a microphone would record**:
```
>>> rec.full_record
array([25.61194502, 25.61194502, 25.61194502, ..., 25.61194502,
       25.61194502, 25.61194502])
```
We also have access to the bounds of noise and quiet as they would be *observed*. These are based off the intervals of time where noise was greater in amplitude than the ambient.

Start and end times of noise:
```
>>> rec.noise_intervals
array([[   1425,    1657],
       [   1964,    2161],
       [   8643,    8828],
       ..., 
       [2414790, 2415052],
       [2415857, 2416100],
       [2416441, 2416683]], dtype=int64)
```

Start and end times of quietude:
```
>>> rec.noise_free_intervals
array([[      0,    1425],
       [   1657,    1964],
       [   2161,    8643],
       ..., 
       [2415052, 2415857],
       [2416100, 2416441],
       [2416683, 2419200]], dtype=int64)
```

---

### Access to acoustic metrics

Though the binarized noise/non-noise time periods are helpful for detailed use cases, more commonly a user may want a few metrics without the fuss of performing the calculations oneself. `AcousticRecord` automatically calculates many of these metrics when the `.add_ambience()` method is used. This gives us three attributes:

A summary of energy-based metrics:
```
>>> rec.SPL_summary_metrics
```
which results in a 2D numpy array of the following values
>[0] one-second broadband sound pressure levels for each noise event <br>
>[1] the equivalent sound pressure level over the duration of the event (Leq, &ast;) <br>
>[2] the sound exposure level of the event <br>
>[3] the median sound pressure level of the event <br>
>[4] the maximum one-second sound pressure level of the event (maximum Leq, 1s) <br>
>[5] the time at which the maximum one-second sound pressure level occurred

A summary of duration-based metrics:
```
>>> rec.duration_summary_metrics
```
which results in a 2D numpy array of the following values
>[0] a list of each event's duration <br>
>[1] the mean duration <br>
>[2] the standard deviation of the durations <br>
>[3] the median duration <br>
>[4] the median absolute deviation of the durations

Finally there is a very simple list of noise-free intervals:
```
>>> rec.nfi_list
```

These can be exceptionally helpful for analyzing the effects of changing human and/or natural conditions on acoustic metrics.
For example, it can be used to show how changing ambient biases the observed distribution of Sound Exposure Levels: <br><br>
<img src="https://github.com/dbetchkal/AcousticRecord/blob/master/SEL_CDFs_with_changing_natural_ambience.png" alt="figure1" class="inline"/>
