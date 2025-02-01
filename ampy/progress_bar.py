import math
import time

class ProgressBar(object):
    def __init__(self, name='', total=100, bar_width = 22, autorender=True):
        self.total = total
        self.progress = 0
        self.name = name
        self.bar_width = bar_width
        self.autorender = autorender
        self.parent_bath_job = None
    
    def on_progress_done(self, progress):
        self.progress += progress 
        if self.progress > self.total:
            self.progress = self.total
        if self.autorender:
            self.print()
        if self.parent_bath_job:
            self.parent_bath_job.on_progress_done(progress)

    def render(self):
        if self.total == 0:
            return
        fraction = self.progress / self.total
        done = math.floor( fraction * (self.bar_width-2))
        percent = math.floor(fraction * 100)
        return '[{}{}] {}{}%'.format( done * '#',
                                    (self.bar_width - 2 - done ) * ' ',
                                    (3 - len(str(percent)) ) * ' ',
                                    percent)

    def print( self ):
        # start from newline begin
        print('\r',end='')
        # clear last line 
        print('' * (len(self.name) + 4 + self.bar_width), end='')
        print('\r',end='') 
        # if progressbarr have a name, print it 
        if self.name != '':
            print(self.name, ':', self.render(),end='')
        else:
            print(self.render)

class ProgressBarBath(object):
    def __init__(self, name, bar_width = 40):
        self.jobs = []
        self.name = name
        self.progress = ProgressBar(name, 0, bar_width=bar_width, autorender=False )
        self.last_render_lines = 0
        self.bar_width = bar_width
    
    def get_subjob(self, name):
        return next( (x for x in self.jobs if x.name == name), None)

    def add_subjob(self, job):
        if isinstance(job, ProgressBar):
            job.parent_bath_job = self
            job.autorender = False
            job.bar_width = self.bar_width
            self.jobs.append(job)
            self.progress.total += job.total
    
    def on_progress_done(self, progress):
        self.progress.on_progress_done(progress)
        self.print()

    def print( self ):
        max_line_width = 0
        for job in self.jobs:
            line_width =  (len(job.name) + 6 + job.bar_width)
            max_line_width = max( max_line_width, line_width)

        # start from newline begin
        print('\r',end='')        
        # return to print origin
        if self.last_render_lines > 0:
            print( '\r\u001b[{n}A\r'.format(n = self.last_render_lines), end='')

        # print overall progress
        print(self.name, ':', self.progress.render())
        self.last_render_lines = 1
        # print subjobs
        for job in self.jobs:
            job_bar = job.render()
            # clear line
            line_width =  (len(job.name) + 4 + job.bar_width)
            print('' * line_width, end='')
            print('\r',end='') 
            print( job_bar, ':', ' ' * (max_line_width - line_width),  job.name)
            self.last_render_lines += 1



if __name__ == '__main__':
    pb  = ProgressBar('reading stuff', 200, 60, True)
    pb_1 = ProgressBar('writing', 100, 22, True)
    pb_2 = ProgressBar('sleeping', 20, 22, True)
    pb_3  = ProgressBar('reading again', 200, 60, True)

    bath = ProgressBarBath('Overall')
    bath.add_subjob(pb)
    bath.add_subjob(pb_1)
    bath.add_subjob(pb_2)
    bath.add_subjob(pb_3)

    for i in range(0, 200):
        pb.on_progress_done(1)
        time.sleep(0.01)

    time.sleep(1)

    for i in range(0, 100):
        pb_1.on_progress_done(1)
        time.sleep(0.01)
    
    time.sleep(1)
    pb_2.on_progress_done(3)
    time.sleep(0.3)
    pb_2.on_progress_done(7)
    time.sleep(0.3)    
    pb_2.on_progress_done(10)

    for i in range(0, 200):
        pb_3.on_progress_done(1)
        time.sleep(0.01)

    print('\n')
