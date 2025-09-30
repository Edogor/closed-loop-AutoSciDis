from sweetbean.stimulus import Text, Fixation, RandomDotPatterns
from sweetbean import Block, Experiment
from sweetbean.variable import TimelineVariable

def stimulus_sequence(timeline):

  # INSTRUCTION BLOCK

  # generate several text stimuli that serve as instructions
  introduction_welcome = Text(text='Welcome to our perception experiment.<br><br> \
                                          Press the SPACE key to continue.', 
                                    choices=[' '])

  introduction_pictures = Text(text='Each picture contains two sets of dots, one left and one right.<br><br>\
                                       Press the SPACE key to continue.', 
                                    choices=[' '])

  introduction_responses = Text(text='You have to indicate whether the two sets contain an equal number of dots.<br><br>\
                                       Press the y-key for yes (equal number) and<br> the n-key for no (unequal number).<br><br>\
                                       Press the SPACE key to continue.', 
                                    choices=[' '])

  introduction_note = Text(text='Note: For each picture, you have only 2 seconds to respond, so respond quickly.<br><br>\
                                       You can only respond with the y and n keys while the dots are shown.<br><br> \
                                       Press the SPACE key to BEGIN the experiment.', 
                                    choices=[' '])


  # create a list of instruction stimuli for the instruction block
  introduction_list = [introduction_welcome, 
                       introduction_pictures, 
                       introduction_responses, 
                       introduction_note]

  # create the instruction block
  instruction_block = Block(introduction_list)

  # EXIT BLOCK

  # create a text stimulus shown at the end of the experiment
  instruction_exit = Text(duration=3000, 
                                  text='Thank you for participating in the experiment.', 
                                  )

  # create a list of instruction stimuli for the exit block
  exit_list = [instruction_exit]

  # create the exit block
  exit_block = Block(exit_list)

  # TASK BLOCK

  # define fixation cross
  fixation = Fixation(1500)

  # define the stimuli features as timeline variables
  dot_stimulus_left = TimelineVariable('dots left')
  dot_stimulus_right = TimelineVariable('dots right')

  # We can define a stimulus as a function of those stimulus features
  rdp = RandomDotPatterns(
      duration=2000,
      number_of_oobs=[dot_stimulus_left, dot_stimulus_right],
      number_of_apertures=2,
      choices=["y", "n"],
      background_color="black",
  )

  # define the sequence of events within a trial
  event_sequence = [fixation, rdp]

  # group trials into blocks
  task_block = Block(event_sequence, timeline)

  # EXPERIMENT

  # define the entire experiment
  experiment = Experiment([instruction_block, task_block, exit_block])

  # return a js string to transfer to autora
  return experiment.to_js_string(as_function=True, is_async=True)