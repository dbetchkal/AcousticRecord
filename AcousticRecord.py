    
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
        Generate a record of noise for every overflight that occurs.
        '''
        
        # create an empty numpy array to hold the event record
        # we'll use one-second time resolution throughout this model
        self.event_record = np.zeros(shape=self.n_days*3600*24)
        
        for Lmax, dur_fwhm in zip(self.Lmax_distribution, self.fwhm_duration_distribution):
            
            # randomly generate the time at which Lmax will occur - the center of the event
            center_time = np.random.randint(self.event_record.size)
            
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
    
    def annotate_events(self):
        
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
            self.noise_intervals = self.contiguous_regions((self.event_record > self.ambient))

            # likewise, 'observe' the contiguous regions of quiet, where pressure from events is less than the ambient level
            self.noise_free_intervals = self.contiguous_regions((self.event_record < self.ambient))

            # then, correct the noise free intervals to be bounded intervals
            # this removes the overlapping seconds shared by noise and quiet (by convention, always in favor of noise)
            self.adjust_noise_free_intervals(self.noise_free_intervals, self.noise_intervals)
            
        
        elif(self.ambient is None):
            
            raise AttributeError('Ambience is undefined. Use of .add_ambience() is prerequisite to .annotate_events()')
        
        
    def add_ambience(self, Lp):
        
        '''
        Define and add ambience - an essential attribute of acoustic environments - to the full record.
        Then, and only then, are simulated observations meaningful.
        
        
        input
        -----
        Lp (numpy array): Sound pressure levels representing the natural energy of an environment.
                          If a numpy array shorter than the record is given, the first value will
                          be used as a constant. This function also accepts other types of signals
                          for ambience. 
        
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
        
        # as soon as we have the full record, let's simulate what we would measure/observe noise
        self.annotate_events()
        
        
    def reset_ambience(self):
        
        self.full_record = self.event_record
        self.ambient = np.zeros(shape=self.n_days*3600*24)
        
    

