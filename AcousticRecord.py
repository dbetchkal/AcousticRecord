    
import numpy as np

class AcousticRecord(object):
    
    def __init__(self, n_days, n_events, seed=None):
        
        self.n_days = n_days
        self.n_events = n_events
        self.duration = n_days*24*3600
        
        if(seed is not None):
            np.random.seed(seed) # for static plots
        
        # create attributes for traffic properties
        # they're written such that they can be re-assigned if desired
        self.Lmax_distribution = np.random.randint(200, 800, size=n_events)/10 # same precision as SLM
        self.fwhm_duration_distribution = np.random.normal(100, 50, size=n_events)
        self.center_times = np.random.randint(self.duration, size=n_events)

        # initialize numpy arrays to hold noise, natural sound, and (eventually) the combination of both
        self.event_record = None
        self.ambient = None
        self.full_record = None
        
        # this attribute stores the total event duration WITHOUT ambience
        self.total_event_duration = 0
        
        # these attributes represent the temporal bounds of a SPLAT record
        # they are intervals of noise and quietude, respectively
        # initial values are None
        self.noise_intervals = None
        self.noise_free_intervals = None

        # arrays to hold summary metrics
        self.SPL_summary_metrics = None
        self.duration_summary_metrics = None
        self.nfi_list = None
        
        
    def point_source(self, Lmax, duration_fwhm):
    
        '''
        Create a one-second resolution point source with center at time zero.
        This is a helper function to simplify use of 'combine_point_sources()'

        inputs
        ------

        Lmax (float): the highest sound pressure level of the event in decibels
        duration_fwhm (float): full width at half-maxium of the event in seconds
        cutoff (float): the lowest sound pressure level of interest (a cutoff,) in decibels
        
        
        outputs
        -------

        event (numpy array): 

        '''
        
        # an event will definitely be 'over' within ±10 times the full width at half-maximum!
        sweep_times = np.arange(-10*duration_fwhm, 10*duration_fwhm, 1)

        # calculate the gauss curve
        event = Lmax*np.exp(-1*np.power(sweep_times, 2)/(2*np.power(duration_fwhm, 2)))

        return event
    
    
    def combine_point_sources(self):
        
        '''
        Generate a continuous record of noise for every overflight that occurs.
        '''
        
        # create an empty numpy array to hold the event record
        # we'll use one-second time resolution throughout this model
        self.event_record = np.zeros(shape=self.n_days*3600*24)
        
        for Lmax, dur_fwhm, center_time in zip(self.Lmax_distribution, self.fwhm_duration_distribution, self.center_times):
            
            point = self.point_source(Lmax, dur_fwhm)
            
            # handle the fact that events can overlap the start/end of the record
            # if the start of the event is less than the beginning, truncate it
            if(-10*dur_fwhm + center_time < 0):
                rec_start = 0
                event_start = np.absolute(-10*dur_fwhm + center_time)
                
            else:
                rec_start = -10*dur_fwhm + center_time
                event_start = 0
            
            # likewise, if the end of the event is longer than the record
            # it'll also need to be truncated
            if(10*dur_fwhm + center_time >= self.event_record.size):
                rec_end = self.event_record.size
                event_end = self.event_record.size - (10*dur_fwhm + center_time) + 1
                
            else:
                rec_end = 10*dur_fwhm + center_time
                event_end = point.size - 1

                
            # handling 
            try: 

                # cast all the indices to integer
                rec_start = int(rec_start)
                rec_end = int(rec_end)
                event_start = int(event_start)
                event_end = int(event_end)
                
                self.event_record[rec_start:rec_end] = 10*np.log10(np.power(10, self.event_record[rec_start:rec_end]/10) 
                                                  + np.power(10, point[event_start:event_end]/10))
                
                # add the event duration to the total event duration
                self.total_event_duration = self.total_event_duration + (event_end - event_start)
                
            except ValueError:
                
                if(np.absolute(self.event_record[rec_start:rec_end].size 
                          - point[event_start:event_end].size) > 1):
                    
                    self.n_events = self.n_events - 1
                    
                    
                
                elif(np.absolute(self.event_record[rec_start:rec_end].size 
                            - point[event_start:event_end].size) == 1):
                
                    event_end = point.size
                    
                    try:
                        
                        self.event_record[rec_start:rec_end] = 10*np.log10(np.power(10, self.event_record[rec_start:rec_end]/10) 
                                                      + np.power(10, point[event_start:event_end]/10))
                        
                        # add the event duration to the total event duration
                        self.total_event_duration = self.total_event_duration + (event_end - event_start)
                    
                    except ValueError:
                        
                        pass

    
    def adjust_noise_free_intervals(self, noise_free_intervals, noise_intervals):

        '''
        In this simulation our convention will be to have closed noise intervals.
        To achieve this, we need to bound our noise free intervals. 

        '''

        nfi_starts = self.noise_free_intervals.T[0]
        nfi_ends = self.noise_free_intervals.T[1]

        # ------- Account for different beginning conditions -----------------------------------------

        # the record begins with noise...
        if(self.noise_intervals[0, 0] == 0):

            # ...the first noise free interval (and thus ALL intervals) need to start one second later
            nfi_starts = nfi_starts + 1


        # the record begins with quietude...
        else:

            # ...the first noise free interval stays the same, and equals zero
            # the rest are + 1
            nfi_starts = nfi_starts + 1
            nfi_starts[0] = 0


        # ------- Account for different ending conditions -----------------------------------------

            # the record ends with noise...
        if(self.noise_intervals[-1, 0] == 0):

            # ...the last noise free interval (and thus ALL intervals) need to end one second earlier
            nfi_ends = nfi_ends - 1


        # the record ends with quietude...
        else:

            # ...the last noise free interval stays the same, and equals zero
            # the rest are - 1
            save = nfi_ends[-1]
            nfi_ends = nfi_ends - 1
            nfi_ends[-1] = save

        
        # reset attribute to these updated, correct values
        self.noise_free_interval = np.array([nfi_starts, nfi_ends]).T
        
    def contiguous_regions(self, condition):
        
        """
        Finds contiguous True regions of the boolean array "condition". Returns
        a 2D array where the first column is the start index of the region and the
        second column is the end index.
        """

        # Find the indicies of changes in "condition"
        d = np.diff(condition)
        idx, = d.nonzero() 

        # We need to start things after the change in "condition". Therefore, 
        # we'll shift the index by 1 to the right.
        idx += 1

        if condition[0]:
            # If the start of condition is True prepend a 0
            idx = np.r_[0, idx]

        if condition[-1]:
            # If the end of condition is True, append the length of the array
            idx = np.r_[idx, condition.size] # Edit

        # Reshape the result into two columns
        idx.shape = (-1,2)
        
        return idx
    
    def annotate_events(self, audibility_buffer=0.0):
        
        '''
        This function divides self.full_record into binary categories: noise, and non-noise.
        
        input
        -----
        Self
        
        
        outputs
        -------
        (1) list SPLs for each event [use self.event_record for each section of self.full_record >= ambient]
        (2) NFIs [use self.event_record < ambient to save arrays from self.full_record]
            
        '''
        
        # we can't annotate events that don't exist
        if(self.event_record == None):
            
            self.combine_point_sources() 
        
        if(self.ambient is not None):
            
            # 'observe' the contiguous regions of noise
            self.noise_intervals = self.contiguous_regions((self.event_record > self.ambient + audibility_buffer))

            # likewise, 'observe' the contiguous regions of quiet, where pressure from events is less than the ambient level
            self.noise_free_intervals = self.contiguous_regions((self.event_record < self.ambient + audibility_buffer))

            # then, correct the noise free intervals to be bounded intervals
            # this removes the overlapping seconds shared by noise and quiet (by convention, always in favor of noise)
            self.adjust_noise_free_intervals(self.noise_free_intervals, self.noise_intervals)
            
        
        elif(self.ambient is None):
            
            raise AttributeError('Ambience is undefined. Use of .add_ambience() is prerequisite to .annotate_events()')
        
        
    def add_ambience(self, Lp, audibility_buffer=0.0):
        
        '''
        Define and add ambience - an essential attribute of acoustic environments - to the full record.
        Then, and only then, are simulated observations meaningful.
        
        
        input
        -----
        Lp (numpy array): Sound pressure levels representing the natural energy of an environment.
                          If a numpy array shorter than the record is given, the first value will
                          be used as a constant. This function also accepts other types of signals
                          for ambience. 

        audibility_buffer (float): A scalar sound pressure level representing a modifier to the
                          annotation conditions of a given user. It will modify 'annotate_events'.
        
        output
        ------
        modifies self.full_record to include background
        
        '''
        
        # if you haven't combined the noise events yet, do that to generate the event record
        if(self.event_record == None):
            
            self.combine_point_sources()
    

        
        # if the user gives only a single value
        if((type(Lp)==float)|(type(Lp)==int)):
            
            # handle input of scalar integers or floating point numbers
            Lp_toUse = np.array(Lp)
            
            # create a repeated numpy array of this value
            self.ambient = np.repeat(Lp_toUse, self.event_record.size)
        
        # raise and error if the array is too short
        elif((len(Lp) < self.event_record.size)):

            raise Exception("The ambient record is not as long as the entire record. Specify either a constant scalar value or a numpy array of shape ("+str(self.duration)+",).")

        # if the user gives ambience defined over the entire record
        elif(Lp.size == self.event_record.size):
            
            self.ambient = Lp
        
        # add the ambience to the energy from noise to get the full record
        self.full_record = 10*np.log10( np.power(10, self.event_record/10) + np.power(10, self.ambient/10) )
        
        # as soon as we have the full record, let's simulate 
        # the noise conditions we would measure/observe
        self.annotate_events(audibility_buffer=audibility_buffer)
        self.calculate_SPL_summary()
        self.calculate_duration_summary()
        self.calculate_nfi_summary()
        
        
    def reset_ambience(self):
        
        self.full_record = self.event_record
        self.ambient = np.zeros(shape=self.n_days*3600*24)
        
    
    def calculate_SPL_summary(self):

        '''
        This function computes sound pressure level metrics for each noise event in `noise_intervals`.
        It's called as part of `add_ambience()` and works behind the scenes.

        inputs
        ------
        self

        outputs
        -------

        a 2D numpy array of sound pressure level metrics as 'observed' in `self.full_record`:

            [0] one-second broadband sound pressure levels for each noise event
            [1] the equivalent sound pressure level over the duration of the event (Leq, *)
            [2] the sound exposure level of the event
            [3] the median sound pressure level of the event
            [4] the maximum one-second sound pressure level of the event (maximum Leq, 1s)
            [5] the time at which the maximum one-second sound pressure level occurred

        '''

        # the indices corresponding to each noise event (note: NOT each aircraft)
        SPL_summary_indices = [np.arange(s, e+1) for s, e in self.noise_intervals]

        # create a 2-D array: the full time series of each event, PLUS summary metrics
        SPL_summary = []
        for SPL_summary_index in SPL_summary_indices:

            # clip out the one-second record for each event and add it to the full list
            SPL_extract = self.event_record[SPL_summary_index]

            # Equivalent Sound Pressure Level (Leq, *)
            Leq = 10*np.log10((1/SPL_extract.size)*np.power(10, SPL_extract/10).sum())

            # Sound Exposure Level (SEL)
            SEL = Leq + 10*np.log10(SPL_extract.size)

            # Median Sound Pressure Level of the Event (L50)
            L50_event = np.percentile(SPL_extract, 50)

            # Maximum Sound Pressure Level of the Event (maximum Leq, 1s)
            # this metric also has precise timing, which we'll capture
            Lmax_event = np.percentile(SPL_extract, 100)
            Lmax_time = SPL_summary_index[np.argwhere(SPL_extract == Lmax_event)][0,0]

            # add all these calculated metrics to the composite list
            SPL_summary.append([SPL_extract, Leq, SEL, L50_event, Lmax_event, Lmax_time])

        out = np.array(SPL_summary).T

        # update the attribute
        self.SPL_summary_metrics = out

        # it's convenient for this function to return the results
        return out

    def calculate_duration_summary(self):

        '''
        This function computes the duration of noise event in `noise_intervals`.
        It's called as part of `add_ambience()` and works behind the scenes.

        inputs
        ------
        self

        outputs
        -------

        a 2D numpy array of sound pressure level metrics as 'observed' in `self.full_record`:

            [0] a list of each event's duration
            [1] the mean duration
            [2] the standard deviation of the durations
            [3] the median duration
            [4] the median absolute deviation of the durations

        '''
    
        # the durations, themselves
        duration_list = self.noise_intervals.T[1] - self.noise_intervals.T[0]
        
        # mean duration
        mean = np.mean(duration_list)
        
        # standard deviation duration
        stdev = np.std(duration_list)
        
        # median duration
        median = np.percentile(duration_list, 50)
        
        # median absolute deviation of duration
        mad = np.percentile(np.absolute(duration_list - median), 50)
        
        # combine the results and update the class attribute
        out = np.array([duration_list, mean, stdev, median, mad])
        
        # update the attribute
        self.duration_summary_metrics = out

        # it's convenient to return the results
        return out

    def calculate_nfi_summary(self):

        '''
        A very simple function to calculate the length of each noise free interval.
        '''

        nfis = self.noise_free_intervals

        # determine the duration of each interval and reassign the attribute
        self.nfi_list = nfis.T[1] - nfis.T[0]