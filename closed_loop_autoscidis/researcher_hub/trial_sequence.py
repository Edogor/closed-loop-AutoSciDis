from sweetpea import Factor, MinimumTrials, CrossBlock, synthesize_trials, CMSGen, experiments_to_dicts

def trial_sequence(num_dots_1, num_dots_2, min_trials):

  # define regular factors
  num_dots_left = Factor('dots left', [num_dots_1, num_dots_2])
  num_dots_right = Factor('dots right', [num_dots_1, num_dots_2])

  # define experimental block
  design = [num_dots_left, num_dots_right]
  crossing = [num_dots_left, num_dots_right]
  constraints = [MinimumTrials(min_trials)]

  block = CrossBlock(design, crossing, constraints)

  # synthesize trial sequence
  experiment = synthesize_trials(block, 1, CMSGen)

  # export as dictionary
  return experiments_to_dicts(block, experiment)[0]