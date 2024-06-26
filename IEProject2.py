import pandas as pd
import numpy as np
from scipy.special import logsumexp
from collections import defaultdict
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

# Load the training label data to analyze and create emission probabilities
try:
    # Loading the label names
    label_names_path = '/content/clsp.lblnames'
    with open(label_names_path, 'r') as file:
        label_names = file.read().splitlines()
    label_names = label_names[1:]  # Skip the title line

    # Loading the training labels
    training_labels_path = '/content/clsp.trnlbls'
    with open(training_labels_path, 'r') as file:
        training_labels = file.read().splitlines()
    training_labels = training_labels[1:]  # Skip the title line

    # Check if we have the expected number of labels
    assert len(label_names) == 256, "Number of label names should be 256."
    assert len(training_labels) == 798, "Number of training labels should be 798."

    # We will calculate the frequency of each label in the training data
    # First we concatenate all labels into one large string
    all_labels_string = ''.join(training_labels)

    # Count the frequency of each label
    label_counts = pd.Series(list(all_labels_string)).value_counts().reindex(label_names, fill_value=0)

    # Convert counts to probabilities by dividing by the total number of labels
    total_labels = label_counts.sum()
    label_probabilities = label_counts / total_labels

    # Check if any label has zero probability
    zero_prob_labels = label_probabilities[label_probabilities == 0]

    # If there are labels with zero probability, we add 1 to each count and recalculate the probabilities
    # Laplace Smoothing
    if not zero_prob_labels.empty:
        label_counts += 1
        label_probabilities = label_counts / label_counts.sum()

    # organize this data into a DataFrame for easier handling
    emission_prob_df = pd.DataFrame({
        'Label': label_names,
        'Count': label_counts,
        'Probability': label_probabilities
    })

    # Check if there are any zero probabilities
    zero_prob_check = emission_prob_df[emission_prob_df['Probability'] == 0]

except Exception as e:
    error_message = str(e)
    emission_prob_df = None
    zero_prob_check = None

emission_prob_df, zero_prob_check, error_message if 'error_message' in locals() else "No error"

# Correcting the approach to process labels in pairs, since each label is two characters long

def process_labels_into_pairs(labels_list):
    """Process the list of labels into pairs."""
    pairs = []
    for labels in labels_list:
        # Split the labels into chunks of 2 characters
        pairs.extend([labels[i:i+2] for i in range(0, len(labels), 2)])
    return pairs

# Process the training labels into pairs
training_label_pairs = process_labels_into_pairs(training_labels)

# Count the frequency of each label pair
label_pair_counts = pd.Series(training_label_pairs).value_counts().reindex(label_names, fill_value=0)

# Convert counts to probabilities by dividing by the total number of label pairs
total_label_pairs = label_pair_counts.sum()
label_pair_probabilities = label_pair_counts / total_label_pairs

# Check if any label pair has zero probability
zero_prob_label_pairs = label_pair_probabilities[label_pair_probabilities == 0]

# If there are labels with zero probability, we add 1 to each count and recalculate the probabilities
if not zero_prob_label_pairs.empty:
    label_pair_counts += 1
    label_pair_probabilities = label_pair_counts / label_pair_counts.sum()

# Create a DataFrame for the emission probabilities
emission_prob_df = pd.DataFrame({
    'Label': label_names,
    'Count': label_pair_counts,
    'Probability': label_pair_probabilities
})

# Check the DataFrame and show if there are any zero probabilities
zero_prob_check = emission_prob_df[emission_prob_df['Probability'] == 0]

emission_prob_df, zero_prob_check, total_label_pairs

# Load the end-point data to analyze and create emission probabilities for the silence HMM (SIL)
try:
    # Loading the end-point information
    end_points_path = '/content/clsp.endpts'
    with open(end_points_path, 'r') as file:
        end_points = file.read().splitlines()
    end_points = end_points[1:]  # Skip the title line

    # Extract silence portions from the label file using the end-point information
    silence_labels = []
    for end_point, label_string in zip(end_points, training_labels):
        i, j = map(int, end_point.split())
        leading_silence = label_string[:i*2]  # Multiply by 2 because each label is 2 characters
        trailing_silence = label_string[j*2:]
        silence_labels.extend(leading_silence)
        silence_labels.extend(trailing_silence)

    # Process the silence labels into pairs
    silence_label_pairs = process_labels_into_pairs(silence_labels)

    # Count the frequency of each label pair for silence
    silence_label_pair_counts = pd.Series(silence_label_pairs).value_counts().reindex(label_names, fill_value=0)

    # Convert counts to probabilities by dividing by the total number of silence label pairs
    total_silence_label_pairs = silence_label_pair_counts.sum()
    silence_label_pair_probabilities = silence_label_pair_counts / total_silence_label_pairs

    # Check if any silence label pair has zero probability
    zero_prob_silence_label_pairs = silence_label_pair_probabilities[silence_label_pair_probabilities == 0]

    # If there are labels with zero probability, we add 1 to each count and recalculate the probabilities
    if not zero_prob_silence_label_pairs.empty:
        silence_label_pair_counts += 1
        silence_label_pair_probabilities = silence_label_pair_counts / silence_label_pair_counts.sum()

    # Create a DataFrame for the silence emission probabilities
    silence_emission_prob_df = pd.DataFrame({
        'Label': label_names,
        'Count': silence_label_pair_counts,
        'Probability': silence_label_pair_probabilities
    })

    # Check the DataFrame and show if there are any zero probabilities
    zero_prob_silence_check = silence_emission_prob_df[silence_emission_prob_df['Probability'] == 0]

except Exception as e:
    silence_emission_prob_df = None
    zero_prob_silence_check = None
    error_message = str(e)

silence_emission_prob_df, zero_prob_silence_check, error_message if 'error_message' in locals() else "No error"

# The end-points file contains two integers per line indicating the range of speech.
# We need to extract the labels before the first integer (leading silence)
# and after the second integer (trailing silence).

def get_silence_labels(end_points, label_strings):
    silence_labels_list = []
    for end_point, label_string in zip(end_points, label_strings):
        i, j = map(int, end_point.split())  # get the indices for leading and trailing silences
        leading_silence = label_string[:i * 2]  # get leading silence labels
        trailing_silence = label_string[j * 2:]  # get trailing silence labels
        silence_labels_list.append(leading_silence + trailing_silence)
    return silence_labels_list

# Get the combined silence labels from leading and trailing silences
silence_labels_combined = get_silence_labels(end_points, training_labels)

# Process these combined silence labels into pairs
silence_label_pairs = process_labels_into_pairs(silence_labels_combined)

# Now, let's count the frequency of each label pair in the silence segments
silence_label_pair_counts = pd.Series(silence_label_pairs).value_counts().reindex(label_names, fill_value=0)

# Convert the counts to probabilities
total_silence_labels = silence_label_pair_counts.sum()
silence_label_pair_probabilities = silence_label_pair_counts / total_silence_labels

# Add 1 to each count if any label has zero probability (Laplace Smoothing)
if (silence_label_pair_probabilities == 0).any():
    silence_label_pair_counts += 1
    silence_label_pair_probabilities = silence_label_pair_counts / silence_label_pair_counts.sum()

# Create a DataFrame for the silence emission probabilities
silence_emission_prob_df = pd.DataFrame({
    'Label': label_names,
    'Count': silence_label_pair_counts,
    'Probability': silence_label_pair_probabilities
})

# Check the DataFrame for zero probabilities
zero_prob_silence_check = silence_emission_prob_df[silence_emission_prob_df['Probability'] == 0]

silence_emission_prob_df, zero_prob_silence_check, total_silence_labels

class HMM:

    def __init__(self, num_states, num_outputs):
        # Potentially useful constants for state and output alphabets
        self.states = range(num_states)  # just use all zero-based index
        self.outputs = range(num_outputs)
        self.num_states = num_states
        self.num_outputs = num_outputs

        # Probability matrices
        self.transitions = None  # key (1, 2) --> prob of s1 going to s2, i.e. p(s1 --> s2) = p(s2|s1) = p(t1)
        self.emissions = None  # key (3, 1, 2) --> prob of emitting 3 from arc (1->2), i.e. p(3|1->2)

        self.non_null_arcs = []  # a list of (ix, iy), where ix->iy is a non-null arc
        # TODO: can it be implemented as an matrix?
        self.null_arcs = dict()  # a dict of d[ix][iy]=p, where ix->iy is a null arc with probability p
        self.topo_order = []  # a list of states in the topo order that we can evaluate alphas properly

        self.output_arc_counts = None
        self.output_arc_counts_null = None

    def reset_counters(self):
        """Reset the training counters to zero."""
        self.transition_counts.fill(0)
        self.emission_counts.fill(0)

    def update_counters(self, alphas, betas, observations):
        """Update counters based on alpha and beta values from the forward-backward algorithm."""
        for t in range(1, len(observations)):
            obs = observations[t - 1]
            for i in range(self.num_states):
                for j in range(self.num_states):
                    if self.transitions[i, j] > 0:  # Only consider non-null transitions
                        # Update transition counter
                        self.transition_counts[i, j] += alphas[t - 1, i] * self.transitions[i, j] * self.emissions[obs, j] * betas[t, j]

                        # Update emission counter
                        self.emission_counts[obs, i, j] += alphas[t - 1, i] * self.transitions[i, j] * self.emissions[obs, j] * betas[t, j]

    def normalize_counters(self):
        """Normalize the counters to turn counts into probabilities."""
        # Normalize transition probabilities
        total_transitions = self.transition_counts.sum(axis=1, keepdims=True)
        self.transitions = np.where(total_transitions > 0, self.transition_counts / total_transitions, 0)

        # Normalize emission probabilities for each transition
        for i in range(self.num_states):
            for j in range(self.num_states):
                total_emissions = self.emission_counts[:, i, j].sum()
                if total_emissions > 0:
                    self.emissions[:, i, j] = self.emission_counts[:, i, j] / total_emissions


    def init_transition_probs(self, transitions):
        """Initialize transition probability matrices"""
        assert self.transitions is None
        self.transitions = transitions
        self._assert_transition_probs()

        for ix, iy in np.ndindex(self.transitions.shape):
            if self.transitions[ix, iy] - 0 > 10e-6:
                if iy < self.num_states:
                    self.non_null_arcs.append((ix, iy))

    def init_emission_probs(self, emission):
        """Initialize emission probability matrices"""
        assert self.emissions is None
        self.emissions = emission
        self._assert_emission_probs()

    def init_null_arcs(self, null_arcs=None):
        if null_arcs is not None:
            self.null_arcs = null_arcs  # note: null_arcs should be a dict

        # topo sort
        count = np.zeros(self.num_states)
        for ix in self.null_arcs.keys():
            for iy in self.null_arcs[ix].keys():
                if iy < self.num_states:
                    count[iy] += 1
        stack = [s for s in self.states if count[s] == 0]
        while len(stack) > 0:
            s = stack.pop()
            self.topo_order.append(s)
            if s not in self.null_arcs:
                continue
            for s_y in self.null_arcs[s]:
                count[s_y] -= 1
                if count[s_y] == 0:
                    stack.append(s_y)
        assert len(self.topo_order) == self.num_states

    def add_null_arc(self, ix, iy, prob):
        if self.null_arcs is None:
            self.null_arcs = dict()

        if ix not in self.null_arcs:
            self.null_arcs[ix] = dict()

        self.null_arcs[ix][iy] = prob

    def _assert_emission_probs(self):
        emission_sum = self.emissions.sum(axis=0)
        for arc in self.non_null_arcs:
            assert emission_sum[arc].sum() - 1 < 10e-6

    def _assert_transition_probs(self):
        for s in self.states:  # except the last state
            null_sum = 0 if s not in self.null_arcs else sum(self.null_arcs[s].values())
            assert self.transitions[s].sum() + null_sum - 1 < 10e-6

    def forward(self, data, init_prob=None):
        # Construct trellis for the forward pass with equally likely initial (stage-0) values, or given init_prob values

        alphas_ = np.zeros((len(data) + 1, self.num_states))  # normalized alphas
        Q = np.ones(len(data) + 1)  # Normalization constants to prevent underflow

        if init_prob is None:  # then assume uniform distribution
            init_prob = np.asarray([1 / self.num_states] * self.num_states)

        # Assumption: there is no null arc at the first stage or last stage
        alphas_[0] = init_prob
        Q[0] = alphas_[0].sum()
        alphas_[0] /= Q[0]

        """
        # Begin forward pass
        for t in range(1, len(data) + 1):
            # Calculate alpha values for each state in this stage
            obs = data[t - 1]   # Note: alpha[t] actually means the prob of generating data[0: t-1]

            # non_null arcs
            alphas_[t] = np.dot(alphas_[t - 1], self.transitions * self.emissions[obs])
            # null arcs, except the final stage
            if t < len(data):
                for s in self.topo_order:
                    if s not in self.null_arcs:
                        continue
                    for s_y in self.null_arcs[s]:
                        alphas_[t][s_y] += alphas_[t][s] * self.null_arcs[s][s_y]

            # Compute next Q factor and normalize alphas in this stage by Qi
            Q[t] = alphas_[t].sum()
            alphas_[t] /= Q[t]
        """
        init_beta = np.ones((self.num_states,))

        betas_ = self.backward(data, Q, init_beta=init_beta)
        self.reset_counters()
        for t in range(1, len(data) + 1):
          obs = data[t - 1]
          step1 = alphas_[t - 1] * (self.transitions * self.emissions[obs]).T
          step2 = betas_[t]
          step3 = (step1.T * step2)

        # Warning message for NaN values
        total_prob = np.sum(step3)
        if np.isnan(total_prob):
            print(f"Warning: Total probability is NaN at time {t}. This indicates a problem with the model.")
            total_prob = 1.0

        self.output_arc_counts[obs] += step3


    def forward_log(self, data, init_log_prob=None):
        # Construct trellis for the forward pass with equally likely initial (stage-0) values, or given init_prob values

        log_alphas = np.empty((len(data) + 1, self.num_states))

        if init_log_prob is None:  # then assume uniform distribution
            init_log_prob = np.asarray([1 / self.num_states] * self.num_states)
            init_log_prob = np.log(init_log_prob)

        log_alphas[0] = init_log_prob

        # Begin forward pass
        for t in range(1, len(data) + 1):
            # Calculate alpha values for each state in this stage
            obs = data[t - 1]   # Note: alpha[t] actually means the prob of generating data[0: t-1]
            trans_matrix = self.transitions * self.emissions[obs]
            # non_null arcs
            for j in range(self.num_states):
                log_alphas[t][j] = logsumexp(log_alphas[t - 1] + np.log(trans_matrix[:, j]))
            # null arcs, except the final stage
            if t < len(data):
                for s in self.topo_order:
                    if s not in self.null_arcs:
                        continue
                    for s_y in self.null_arcs[s]:
                        log_alphas[t][s_y] = logsumexp([
                            log_alphas[t][s_y],
                            log_alphas[t][s] + np.log(self.null_arcs[s][s_y])
                        ])

        return log_alphas

    def backward(self, data, Q, init_beta=None):
        # Construct trellis for the forward pass with equalliy likely initial (stage-0) values

        betas_ = np.zeros((len(data) + 1, self.num_states))  # normalized betas

        if init_beta is None:
            betas_[-1] = [1] * self.num_states
        else:
            betas_[-1] = init_beta  # This should be an np array

        betas_[-1] = betas_[-1] / Q[-1]

        for t in range(len(data) - 1, -1, -1):
            # Calculate beta values for each state in this stage
            obs = data[t]  # Note: beta[t] actually means the prob of generating data[t:]
            betas_[t] = np.dot(betas_[t + 1], (self.transitions * self.emissions[obs]).T)

            # null arcs
            for s in reversed(self.topo_order):
                if s not in self.null_arcs:
                    continue
                for s_y in self.null_arcs[s]:
                    betas_[t][s] += betas_[t][s_y] * self.null_arcs[s][s_y]

            betas_[t] /= Q[t]

        # print("betas", betas)
        return betas_

    def backward_log(self, data, init_log_beta=None):
        # Construct trellis for the forward pass with equalliy likely initial (stage-0) values

        log_betas = np.empty((len(data) + 1, self.num_states))

        if init_log_beta is None:
            log_betas[-1] = np.zeros(self.num_states)
        else:
            log_betas[-1] = init_log_beta

        for t in range(len(data) - 1, -1, -1):
            # Calculate beta values for each state in this stage
            obs = data[t]
            for j in range(self.num_states):
                log_betas[t][j] = logsumexp(log_betas[t + 1] + np.log(self.emissions[obs][j]) + np.log(self.transitions[j]))

            # null arcs
            for s in reversed(self.topo_order):
                if s not in self.null_arcs:
                    continue
                for s_y in self.null_arcs[s]:
                    log_betas[t][s] = logsumexp([
                        log_betas[t][s],
                        log_betas[t][s_y] + np.log(self.null_arcs[s][s_y])
                    ])

        # print("betas", betas)
        return log_betas

    def un_norm_alphas_(self, alphas_, Q):
        alphas = np.copy(alphas_)
        cur_q = 1
        for t in range(alphas.shape[0]):
            cur_q *= Q[t]
            alphas[t] *= cur_q
        return alphas

    def un_norm_betas_(self, betas_, Q):
        betas = np.copy(betas_)
        cur_q = 1
        for t in range(betas.shape[0] - 2, -1, -1):
            cur_q *= Q[t + 1]
            betas[t] *= cur_q
        return betas



    def forward_backward(self, train, init_prob=None, init_beta=None, update_params=True):
    # Perform forward and backward passes to calculate alpha and beta values

      alphas_, Q = self.forward(train, init_prob=init_prob)
      betas_ = self.backward(train, Q, init_beta=init_beta)

    # Initialize output arc counts
      self.reset_counters()

    # Compute non-null arc posteriors P_{t}^{*}(arc) and update counts
      for t in range(1, len(train) + 1):
        obs = train[t - 1]
        step1 = alphas_[t - 1] * (self.transitions * self.emissions[obs]).T
        step2 = betas_[t]
        step3 = (step1.T * step2)
        assert np.sum(step3) - 1 < 1e-6  # Check normalization
        self.output_arc_counts[obs] += step3

    # Compute null arc posteriors and update counts
      for t in range(1, len(train)):  # no null transition on first and last step
        for ix in self.null_arcs.keys():
            for iy in self.null_arcs[ix].keys():
                p = alphas_[t][ix] * self.null_arcs[ix][iy] * betas_[t][iy] * Q[t]
                self.output_arc_counts_null[ix][iy] += p

    # Update parameters if specified
      if update_params:
        self.update_params()

      return alphas_, betas_, Q

    def reset_counters(self):
        self.output_arc_counts = np.zeros((self.num_outputs, self.num_states, self.num_states))
        self.output_arc_counts_null = defaultdict(lambda: defaultdict(lambda: 0))

    def set_counters(self, another_output_arc_counts, another_output_arc_counts_null):
        self.output_arc_counts += another_output_arc_counts

        for ix in another_output_arc_counts_null.keys():
            for iy in another_output_arc_counts_null[ix].keys():
                self.output_arc_counts_null[ix][iy] += another_output_arc_counts_null[ix][iy]

    def update_params(self):
        self.emissions = self.output_arc_counts / self.output_arc_counts.sum(axis=0)
        np.nan_to_num(self.emissions, copy=False, nan=0.0)
        self._assert_emission_probs()

        trans_sum = self.output_arc_counts.sum(axis=0)
        trans_sum_row = trans_sum.sum(axis=1)
        trans_new = np.zeros_like(self.transitions, dtype=np.float64)
        for index, x in np.ndenumerate(self.transitions):
            ix, iy = index
            trans_new[index] = trans_sum[index] / (trans_sum_row[ix] + sum(self.output_arc_counts_null[ix].values()))
        self.transitions = trans_new

        for ix in self.null_arcs.keys():
            for iy in self.null_arcs[ix].keys():
                self.null_arcs[ix][iy] = \
                    self.output_arc_counts_null[ix][iy] / (trans_sum_row[ix] + sum(self.output_arc_counts_null[ix].values()))

        self._assert_transition_probs()

    def log_likelihood(self, alphas_, betas_, Q):
        return np.log((alphas_[-1] * betas_[-1] * Q[-1]).sum()) + np.log(Q).sum()

    def compute_log_likelihood(self, data, init_prob, init_beta):
        alphas_, Q = self.forward(data, init_prob=init_prob)
        return np.log((alphas_[len(data)] * init_beta).sum()) + np.log(Q).sum()

    def compute_sequence_log_likelihood(self, alphas):
        """Compute the log likelihood of a single sequence given the alphas matrix."""
        # Assuming alphas[-1] contains the alpha values for the last time step
        return np.log(alphas[-1].sum())

# Initialize the HMM for each letter with the given transition probabilities and emission probabilities

# Define the transition probability matrix for a 3-state HMM as given in the project description
transition_prob_matrix = np.array([[0.8, 0.2, 0.0],
                                   [0.0, 0.8, 0.2],
                                   [0.0, 0.0, 0.8]])

# Create HMM instances for each letter and initialize them
letter_HMMs = {}
for letter in 'abcdefghijklmnopqrstuvwxyz':
    if letter in ['k', 'q', 'z']:  # Exclude the letters [k], [q], and [z]
        continue

    # Create a new HMM instance for the letter
    letter_hmm = HMM(num_states=3, num_outputs=256)

    # Initialize the transition probabilities
    # This transition matrix is shared by all non-null arcs in the HMM for the letter
    letter_hmm.transitions = np.array([[0.8, 0.2, 0.0],
                                       [0.0, 0.8, 0.2],
                                       [0.0, 0.0, 0.8]])

    # Initialize emission probabilities
    # Each state can emit any of the outputs with probabilities based on the unigram frequency
    # Here, we create a uniform distribution for emissions as an example
    # The actual emission probabilities would be based on the specific unigram frequencies of the labels
    uniform_emission_prob = np.full((256, 3), 1/256)  # We have 256 possible outputs
    # Transpose the emission matrix to match the expected shape (num_outputs, num_states)
    letter_hmm.emissions = uniform_emission_prob.T

    # Store the HMM in the dictionary
    letter_HMMs[letter] = letter_hmm

# Now we have a dictionary with an HMM for each letter (except [k], [q], and [z])
# These HMMs are initialized with the given transition matrix and a placeholder for emission probabilities
letter_HMMs.keys()  # Display the letters for which HMMs have been created

# Define the transition probability matrix for a 5-state HMM for silence as given in the project description
silence_transition_prob_matrix = np.array([
    [0.25, 0.25, 0.25, 0.25, 0.00],
    [0.00, 0.25, 0.25, 0.25, 0.25],
    [0.00, 0.00, 0.25, 0.25, 0.25],
    [0.00, 0.00, 0.00, 0.25, 0.25],
    [0.00, 0.00, 0.00, 0.00, 0.75]
])

# Create a new HMM instance for silence
silence_hmm = HMM(num_states=5, num_outputs=256)

# Initialize the transition probabilities for the silence HMM
silence_hmm.transitions = silence_transition_prob_matrix

# Initialize the emission probabilities for the silence HMM
# We will use the previously calculated probabilities for the silence labels
# Here we reshape the probabilities to match the expected shape (num_outputs, num_states)
silence_emission_prob_matrix = np.tile(silence_emission_prob_df['Probability'].fillna(0).to_numpy(), (5, 1)).T

# Initialize the emission probabilities in the silence HMM
silence_hmm.emissions = silence_emission_prob_matrix

# The silence HMM ('SIL') is now initialized with the given transition matrix and emission probabilities based on silence segments
silence_hmm

def initialize_hmm(hmm, num_states, num_outputs, type='letter'):
    """
    Initializes the transition and emission matrices for an HMM.

    :param hmm: An instance of the HMM class.
    :param num_states: Number of states in the HMM.
    :param num_outputs: Number of output symbols (usually the size of the vocabulary or feature set).
    :param type: 'letter' for letter HMMs or 'silence' for the silence HMM.
    """
    # Create transition matrix
    hmm.transitions = np.zeros((num_states, num_states))
    if type == 'letter':
        # Simple left-to-right model for letters
        for i in range(num_states - 1):
            hmm.transitions[i, i] = 0.5  # Stay in the same state
            hmm.transitions[i, i + 1] = 0.5  # Move to next state
        hmm.transitions[num_states - 1, num_states - 1] = 1.0  # Last state loops to itself
    elif type == 'silence':
        # More complex model can be used for silence
        for i in range(num_states - 1):
            hmm.transitions[i, i] = 0.7
            hmm.transitions[i, i + 1] = 0.3
        hmm.transitions[num_states - 1, num_states - 1] = 1.0

    # Create emission matrix
    hmm.emissions = np.full((num_outputs, num_states), 1.0 / num_outputs)  # Uniformly distributed emissions

    # Validate initialization
    assert np.allclose(hmm.transitions.sum(axis=1), 1), "Transition probabilities must sum to 1"
    assert np.allclose(hmm.emissions.sum(axis=0), 1), "Emission probabilities must sum to 1"


# Assume letter_HMMs is a dictionary of HMM objects for each letter
for letter in "abcdefghijklmnopqrstuvwxyz":
    if letter not in "kqz":  # Excluding 'k', 'q', 'z'
        initialize_hmm(letter_HMMs[letter], 3, 256, 'letter')

# Initialize silence HMM
initialize_hmm(silence_hmm, 5, 256, 'silence')

print("HMMs initialized successfully.")

def check_hmm_initialization(hmm):
    # Check if transitions and emissions are initialized
    if hmm.transitions is None or hmm.emissions is None:
        return False, "Transitions or emissions are not initialized."
    # Check if transitions are properly normalized
    if not np.allclose(hmm.transitions.sum(axis=1), 1):
        return False, "Transition probabilities are not normalized."
    # Check if emissions are properly normalized
    if not np.allclose(hmm.emissions.sum(axis=0), 1):
        return False, "Emission probabilities are not normalized."
    return True, "HMM is properly initialized."

# Example usage:
# Assuming 'letter_HMMs' is a dictionary of HMM objects for each letter and 'silence_HMM' for silence
all_initialized = True
for letter, hmm in letter_HMMs.items():
    is_initialized, message = check_hmm_initialization(hmm)
    if not is_initialized:
        print(f"Initialization error in {letter} HMM: {message}")
        all_initialized = False

# Check silence HMM
is_initialized, message = check_hmm_initialization(silence_hmm)
if not is_initialized:
    print(f"Initialization error in silence HMM: {message}")
    all_initialized = False

if all_initialized:
    print("All HMMs are properly initialized.")
else:
    print("Some HMMs are not properly initialized.")

"""
def initialize_combined_hmm(word, letter_HMMs, silence_HMM):
    # Calculate total number of states: 10 for initial and final silence, plus 3 for each letter
    num_states = 5 + 5 + 3 * len(word)

    # Create a new combined HMM
    combined_hmm = HMM(num_states, 256)  # Assuming 256 is the number of possible outputs

    # Initialize transitions and emissions matrices for the combined HMM
    combined_hmm.transitions = np.zeros((num_states, num_states))
    combined_hmm.emissions = np.zeros((256, num_states))  # (outputs, states)

    # Initialize transitions and emissions for the initial silence HMM
    combined_hmm.transitions[:5, :5] = silence_HMM.transitions
    combined_hmm.emissions[:, :5] = silence_HMM.emissions

    # Initialize transitions and emissions for each letter HMM
    current_state_index = 5  # Start index after the initial silence HMM
    for letter in word:
        letter_hmm = letter_HMMs[letter]
        end_state_index = current_state_index + 3  # Each letter HMM has 3 states

        # Set transitions for this letter HMM
        combined_hmm.transitions[current_state_index:end_state_index, current_state_index:end_state_index] = letter_hmm.transitions

        # Set emissions for this letter HMM
        combined_hmm.emissions[:, current_state_index:end_state_index] = letter_hmm.emissions

        # Update the current state index to the end of this letter HMM
        current_state_index = end_state_index

    # Initialize transitions and emissions for the final silence HMM
    combined_hmm.transitions[-5:, -5:] = silence_HMM.transitions
    combined_hmm.emissions[:, -5:] = silence_HMM.emissions

    return combined_hmm

# Example usage
word = "also"
letter_HMMs = {char: HMM(3, 256) for char in "abcdefghijklmnopqrstuvwxyz" if char not in "kqz"}  # Dummy HMMs for letters
silence_HMM = HMM(5, 256)  # Dummy HMM for silence
combined_hmm = initialize_combined_hmm(word, letter_HMMs, silence_hmm)
"""

#Initialize the Combined HMM and Concatenate Transition Probabilities

def initialize_combined_hmm(word, letter_HMMs, silence_HMM):
    # Calculate total number of states: 10 for initial and final silence, plus 3 for each letter
    num_states = 5 + 5 + 3 * len(word)

    # Create a new combined HMM
    combined_hmm = HMM(num_states, 256)  # Assuming 256 is the number of possible outputs

    # Initialize transitions and emissions matrices for the combined HMM
    combined_hmm.transitions = np.zeros((num_states, num_states))
    combined_hmm.emissions = np.zeros((256, num_states))  # (outputs, states)

    # Initialize transitions and emissions for the initial silence HMM
    combined_hmm.transitions[:5, :5] = silence_HMM.transitions
    combined_hmm.emissions[:, :5] = silence_HMM.emissions

    # Initialize transitions and emissions for each letter HMM
    current_state_index = 5  # Start index after the initial silence HMM
    for letter in word:
        letter_hmm = letter_HMMs[letter]
        end_state_index = current_state_index + 3  # Each letter HMM has 3 states

        # Link the last state of the previous HMM to the first state of the current letter HMM
        combined_hmm.transitions[current_state_index - 1, current_state_index] = 1.0

        # Set transitions for this letter HMM
        combined_hmm.transitions[current_state_index:end_state_index, current_state_index:end_state_index] = letter_hmm.transitions

        # Set emissions for this letter HMM
        combined_hmm.emissions[:, current_state_index:end_state_index] = letter_hmm.emissions

        # Update the current state index to the end of this letter HMM
        current_state_index = end_state_index

    # Link the last state of the last letter HMM to the first state of the final silence HMM
    combined_hmm.transitions[current_state_index - 1, -5] = 1.0

    # Initialize transitions and emissions for the final silence HMM
    combined_hmm.transitions[-5:, -5:] = silence_HMM.transitions
    combined_hmm.emissions[:, -5:] = silence_HMM.emissions

    return combined_hmm

# Example usage
word = "also"
letter_HMMs = {char: HMM(3, 256) for char in "abcdefghijklmnopqrstuvwxyz" if char not in "kqz"}  # Dummy HMMs for letters
silence_HMM = HMM(5, 256)  # Dummy HMM for silence
combined_hmm = initialize_combined_hmm(word, letter_HMMs, silence_HMM)

#gives error
def check_hmm_normalization(hmm):
    """
    Check if the transition and emission matrices of an HMM are properly normalized.
    """
    # Check transition probabilities
    for state in range(hmm.num_states):
        if not np.isclose(hmm.transitions[state].sum(), 1):
            return False, f"Transition probabilities for state {state} are not properly normalized."

    # Check emission probabilities
    for state in range(hmm.num_states):
        if not np.isclose(hmm.emissions[:, state].sum(), 1):
            return False, f"Emission probabilities for state {state} are not properly normalized."

    return True, "HMM transition and emission matrices are properly normalized."


# Verify normalization for the combined HMM
is_normalized, message = check_hmm_normalization(combined_hmm)
if is_normalized:
    print("Combined HMM transition and emission matrices are properly normalized.")
else:
    print("Normalization check failed:", message)

def initialize_combined_hmm(word, letter_HMMs, silence_HMM):
    num_states = 5 + 5 + 3 * len(word)  # 10 for silences + 3 for each letter

    # Create a new combined HMM with zero-initialized matrices
    combined_hmm = HMM(num_states, 256)
    combined_hmm.transitions = np.zeros((num_states, num_states))
    combined_hmm.emissions = np.zeros((256, num_states))

    # Initialize initial silence HMM
    combined_hmm.transitions[:5, :5] = silence_HMM.transitions
    combined_hmm.emissions[:, :5] = silence_HMM.emissions

    # Initialize each letter HMM
    current_state_index = 5
    for letter in word:
        letter_hmm = letter_HMMs[letter]
        end_state_index = current_state_index + 3

        # Link previous to current letter HMM
        combined_hmm.transitions[current_state_index - 1, current_state_index] = 1.0

        # Set current letter HMM transitions and emissions
        combined_hmm.transitions[current_state_index:end_state_index, current_state_index:end_state_index] = letter_hmm.transitions
        combined_hmm.emissions[:, current_state_index:end_state_index] = letter_hmm.emissions

        current_state_index = end_state_index

    # Final silence HMM
    combined_hmm.transitions[current_state_index - 1, -5:] = 1.0
    combined_hmm.transitions[-5:, -5:] = silence_HMM.transitions
    combined_hmm.emissions[:, -5:] = silence_HMM.emissions

    return combined_hmm

# Then you can re-run the normalization check
combined_hmm = initialize_combined_hmm(word, letter_HMMs, silence_HMM)
is_normalized, message = check_hmm_normalization(combined_hmm)

def initialize_combined_hmm(word, letter_HMMs, silence_HMM):
    # Calculate total number of states: 5 for initial and final silence, plus 3 for each letter
    num_states = 5 + 5 + 3 * len(word)

    # Create a new combined HMM
    combined_hmm = HMM(num_states, 256)  # Assuming 256 is the number of possible outputs

    # Initialize transitions and emissions matrices for the combined HMM
    combined_hmm.transitions = np.zeros((num_states, num_states))
    combined_hmm.emissions = np.zeros((256, num_states))  # (outputs, states)

    # Set transition probabilities consistent with the specified matrix
    for i in range(num_states):
        if i % 3 == 2 and (i >= 5 and i < num_states - 5):  # State is the last in a letter HMM (not including silences)
            combined_hmm.transitions[i, i] = 0.8  # Self-loop
            combined_hmm.transitions[i, i + 1] = 0.2  # Transition to the next state (non-emitting)
        elif i < num_states - 1:  # For all other states except the final state
            combined_hmm.transitions[i, i:i+3] = transition_prob_matrix[i % 3]

    # Initialize transitions and emissions for the initial silence HMM
    combined_hmm.transitions[:5, :5] = silence_HMM.transitions
    combined_hmm.emissions[:, :5] = silence_HMM.emissions

    # Initialize transitions and emissions for each letter HMM
    current_state_index = 5  # Start index after the initial silence HMM
    for letter in word:
        letter_hmm = letter_HMMs[letter]
        end_state_index = current_state_index + 3  # Each letter HMM has 3 states

        # Set transitions for this letter HMM
        combined_hmm.transitions[current_state_index:end_state_index, current_state_index:end_state_index] = letter_hmm.transitions

        # Set emissions for this letter HMM
        combined_hmm.emissions[:, current_state_index:end_state_index] = letter_hmm.emissions

        current_state_index = end_state_index

    # Final state of the last letter HMM should not have a non-emitting transition
    combined_hmm.transitions[current_state_index - 1, current_state_index - 1] = 1.0

    # Initialize transitions and emissions for the final silence HMM
    combined_hmm.transitions[-5:, -5:] = silence_HMM.transitions
    combined_hmm.emissions[:, -5:] = silence_HMM.emissions

    return combined_hmm

def check_transitions_sum_to_one(hmm):
    for i in range(hmm.num_states):
        transition_sum = hmm.transitions[i].sum()
        if not np.isclose(transition_sum, 1):
            print(f"State {i} transition sum: {transition_sum}")  # This should print 1 for every state
            assert np.isclose(transition_sum, 1), f"Transition probabilities for state {i} do not sum to 1"

for state in range(hmm.num_states):
    print(f"State {state} transition sum: {hmm.transitions[state].sum()}")
    print(f"State {state} emission sum: {hmm.emissions[:, state].sum()}")

#doesnt give correct answer
def check_hmm_normalization(hmm):
    """
    Check if the transition and emission matrices of an HMM are properly normalized.
    """
    # Check transition probabilities
    for state in range(hmm.num_states):
        if not np.isclose(hmm.transitions[state].sum(), 1):
            return False, f"Transition probabilities for state {state} are not properly normalized."

    # Check emission probabilities
    for state in range(hmm.num_states):
        if not np.isclose(hmm.emissions[:, state].sum(), 1):
            return False, f"Emission probabilities for state {state} are not properly normalized."

    return True, "HMM transition and emission matrices are properly normalized."


# Verify normalization for the combined HMM
is_normalized, message = check_hmm_normalization(combined_hmm)
if is_normalized:
    print("Combined HMM transition and emission matrices are properly normalized.")
else:
    print("Normalization check failed:", message)

#Concatenating Emission Probabilities

# Initialize emissions for each HMM
current_state_index = 5  # Start index after the initial silence HMM
for letter in word:
    letter_hmm = letter_HMMs[letter]
    end_state_index = current_state_index + 3  # Each letter HMM has 3 states

    # Set emissions for this letter HMM
    combined_hmm.emissions[:, current_state_index:end_state_index] = letter_hmm.emissions

    # Update the current state index to the end of this letter HMM
    current_state_index = end_state_index

# Handle null transitions
current_state_index = 5  # Start index after the initial silence HMM
for letter in word:
    letter_hmm = letter_HMMs[letter]
    end_state_index = current_state_index + 3  # Each letter HMM has 3 states

    # Adjust null transitions for this letter HMM
    for start_state, null_transitions in letter_hmm.null_arcs.items():
        for end_state, prob in null_transitions.items():
            # Update start and end state indices to reflect their position in the combined HMM
            start_state_combined = start_state + current_state_index
            end_state_combined = end_state + current_state_index
            combined_hmm.add_null_arc(start_state_combined, end_state_combined, prob)

    # Update the current state index to the end of this letter HMM
    current_state_index = end_state_index

# Set the Topological Order
combined_hmm.topo_order = []

# Add states from the initial silence HMM
combined_hmm.topo_order.extend(range(5))

# Add states from each letter HMM
current_state_index = 5  # Start index after the initial silence HMM
for letter in word:
    end_state_index = current_state_index + 3  # Each letter HMM has 3 states
    combined_hmm.topo_order.extend(range(current_state_index, end_state_index))
    current_state_index = end_state_index

# Add states from the final silence HMM
combined_hmm.topo_order.extend(range(current_state_index, current_state_index + 5))

# Verify the length of the topological order matches the total number of states
# Verify the length of the topological order matches the total number of states
assert len(combined_hmm.topo_order) == combined_hmm.num_states, "Topological order length mismatch"


# Print the topological order (optional)
print("Topological order of states in the combined HMM:", combined_hmm.topo_order)

def check_topological_order(topo_order, num_states):
    # Check if the order is sequential without any gaps or repetitions
    seen_states = set()
    prev_state = None
    for state in topo_order:
        # Check for gaps or repetitions
        if prev_state is not None and state != prev_state + 1:
            return False, "Topological order contains gaps or repetitions."
        prev_state = state

        # Check for repetitions
        if state in seen_states:
            return False, "Topological order contains repetitions."
        seen_states.add(state)

    # Check if all states are present
    if len(seen_states) != num_states:
        return False, "Topological order does not contain all states."

    return True, "Topological order is valid."

# Assuming combined_hmm.topo_order contains the topological order list
is_valid, message = check_topological_order(combined_hmm.topo_order, combined_hmm.num_states)
print(message)

#Load the Data Files
def load_file(file_path):
    with open(file_path, 'r') as file:
        data = file.readlines()
    # Remove title-line and strip newlines
    data = [line.strip() for line in data[1:]]
    return data

trnscr = load_file('clsp.trnscr')
trnlbls = load_file('clsp.trnlbls')

#Sort and Group Utterances by Words

# This assumes that trnscr and trnlbls are already aligned line by line
assert len(trnscr) == len(trnlbls)

# Combine them into pairs for sorting
training_pairs = list(zip(trnscr, trnlbls))

# Sort by the script (the words spoken)
training_pairs.sort(key=lambda x: x[0])

# Then group by the word
from itertools import groupby
grouped_data = {key: list(group) for key, group in groupby(training_pairs, lambda x: x[0])}

# Now, `grouped_data` is a dictionary where each key is a word, and the value is a list of (word, label sequence) pairs

#Extract Label Sequences and Count Occurrences for Each Word

from collections import Counter

# Count the number of occurrences for each label (to initialize the emission distributions later)
label_counts = Counter()

for word, sequences in grouped_data.items():
    label_sequences = [label_sequence for _, label_sequence in sequences]
    # Flatten the list of label sequences to count individual labels
    for sequence in label_sequences:
        label_counts.update(sequence.split())

# You may want to normalize these counts or convert them to probabilities to initialize the emission distributions.

def initialize_combined_hmm(word, letter_HMMs, silence_HMM):
    # Calculate total number of states: 5 for initial and final silence, plus 3 for each letter
    num_states = 5 + 5 + 3 * len(word)

    # Create a new combined HMM
    combined_hmm = HMM(num_states, 256)  # Assuming 256 is the number of possible outputs

    # Initialize transitions and emissions matrices for the combined HMM
    combined_hmm.transitions = np.zeros((num_states, num_states))
    combined_hmm.emissions = np.zeros((256, num_states))  # (outputs, states)

    # Initialize transitions and emissions for the initial silence HMM
    combined_hmm.transitions[:5, :5] = silence_HMM.transitions
    combined_hmm.emissions[:, :5] = silence_HMM.emissions

    # Initialize transitions and emissions for each letter HMM
    current_state_index = 5  # Start index after the initial silence HMM
    for letter in word:


        if letter not in letter_HMMs:
            raise ValueError(f"Letter '{letter}' is not a valid key in letter_HMMs dictionary.")

        letter_hmm = letter_HMMs[letter]
        end_state_index = current_state_index + 3  # Each letter HMM has 3 states

        # Set transitions for this letter HMM
        combined_hmm.transitions[current_state_index:end_state_index, current_state_index:end_state_index] = letter_hmm.transitions

        # Set emissions for this letter HMM
        combined_hmm.emissions[:, current_state_index:end_state_index] = letter_hmm.emissions

        current_state_index = end_state_index

    # Set transition probabilities consistent with the specified matrix
    for i in range(5, num_states - 5):  # Avoid the silence states at the beginning and end
        if (i - 5) % 3 == 2:  # State is the last in a letter HMM
            combined_hmm.transitions[i, i] = 0.8  # Self-loop
            if i + 1 < num_states - 5:  # If not the last letter state
                combined_hmm.transitions[i, i + 1] = 0.2  # Transition to the next state (non-emitting)
        else:  # For other states within a letter HMM
            combined_hmm.transitions[i, i:i+3] = transition_prob_matrix[(i - 5) % 3]

    # Initialize transitions and emissions for the final silence HMM
    combined_hmm.transitions[-5:, -5:] = silence_HMM.transitions
    combined_hmm.emissions[:, -5:] = silence_HMM.emissions

    return combined_hmm

def load_training_data(script_path, labels_path):
    # Load the script file which contains the words
    with open(script_path, 'r') as file:
        words = [line.strip() for line in file.readlines()][1:]  # skipping the title line

    # Load the labels file which contains the corresponding labels for each word
    with open(labels_path, 'r') as file:
        labels = [line.strip() for line in file.readlines()][1:]  # skipping the title line

    # Group labels by words assuming each word in script corresponds to a label line
    training_data = {word: [] for word in set(words)}
    for word, label in zip(words, labels):
        training_data[word].append(label)

    return training_data

# Path to the training data files
script_path = '/content/clsp.trnscr'
labels_path = '/content/clsp.trnlbls'

# Load training data
training_data = load_training_data(script_path, labels_path)

# Words are the unique entries in the script file
words = list(training_data.keys())

#Just trying to get a graph this does not include the forward and backward algo
# Define a function to load the script file and extract unique words
def load_words(script_path):
    with open(script_path, 'r') as file:
        # Skip the title line and read all words
        words = [line.strip() for line in file.readlines()[1:]]  # assuming the first line is a header
    return list(set(words))  # Return unique words

# Path to the script file containing words
script_path = '/content/clsp.trnscr'

# Load the unique words from the script file
words = load_words(script_path)

# The rest of your code remains the same
def train_combined_hmms(words, letter_HMMs, silence_HMM, num_iterations):
    combined_hmms = {}
    log_likelihoods = defaultdict(list)

    # Initialize combined HMMs for each word
    for word in words:
        combined_hmms[word] = initialize_combined_hmm(word, letter_HMMs, silence_HMM)

    # Simulate training iterations
    for _ in range(num_iterations):
        for word, hmm in combined_hmms.items():
            # Assuming random training data for demonstration; replace this with actual forward-backward implementation
            current_log_likelihood = np.random.random()
            log_likelihoods[word].append(current_log_likelihood)

    return combined_hmms, log_likelihoods

# Initialize dummy HMMs for letters and silence
letter_HMMs = {chr(i+97): HMM(3, 256) for i in range(26)}
silence_HMM = HMM(5, 256)

# Simulate training
num_iterations = 10
combined_hmms, log_likelihoods = train_combined_hmms(words, letter_HMMs, silence_HMM, num_iterations)

# Plot log likelihoods for each word
for word, likelihoods in log_likelihoods.items():
    plt.plot(likelihoods, label=f'Word: {word}')

plt.xlabel('Iteration')
plt.ylabel('Log Likelihood')
plt.title('Log Likelihood over Iterations of Combined HMM Training')
plt.legend()
plt.show()

#Training with the help of placeholders, does not work


# Define the path to your data files
script_file_path = 'path_to/clsp.trnscr'
label_file_path = 'path_to/clsp.trnlbls'
label_names_file_path = 'path_to/clsp.lblnames'
endpoints_file_path = 'path_to/clsp.endpts'

# Load and preprocess your data
try:
    # Load label names
    with open(label_names_file_path, 'r') as file:
        label_names = file.read().splitlines()
    label_names = label_names[1:]  # Skip the title line

    # Load training labels
    with open(label_file_path, 'r') as file:
        training_labels = file.read().splitlines()
    training_labels = training_labels[1:]  # Skip the title line

    # Process training labels into pairs
    training_label_pairs = process_labels_into_pairs(training_labels)

    # Count the frequency of each label pair
    label_pair_counts = pd.Series(training_label_pairs).value_counts().reindex(label_names, fill_value=0)

    # Convert counts to probabilities
    total_label_pairs = label_pair_counts.sum()
    label_pair_probabilities = label_pair_counts / total_label_pairs

    # Perform Laplace Smoothing if needed
    if (label_pair_probabilities == 0).any():
        label_pair_counts += 1
        label_pair_probabilities = label_pair_counts / label_pair_counts.sum()

    # Create a DataFrame for the emission probabilities
    emission_prob_df = pd.DataFrame({
        'Label': label_names,
        'Count': label_pair_counts,
        'Probability': label_pair_probabilities
    })

    # Load endpoints
    with open(endpoints_file_path, 'r') as file:
        endpoints = file.read().splitlines()
    endpoints = endpoints[1:]  # Skip the title line

    # Extract silence labels using endpoints
    silence_labels_combined = get_silence_labels(endpoints, training_labels)

    # Process silence labels into pairs
    silence_label_pairs = process_labels_into_pairs(silence_labels_combined)

    # Count the frequency of each label pair in silence segments
    silence_label_pair_counts = pd.Series(silence_label_pairs).value_counts().reindex(label_names, fill_value=0)

    # Convert counts to probabilities
    total_silence_labels = silence_label_pair_counts.sum()
    silence_label_pair_probabilities = silence_label_pair_counts / total_silence_labels

    # Perform Laplace Smoothing if needed
    if (silence_label_pair_probabilities == 0).any():
        silence_label_pair_counts += 1
        silence_label_pair_probabilities = silence_label_pair_counts / silence_label_pair_counts.sum()

    # Create a DataFrame for silence emission probabilities
    silence_emission_prob_df = pd.DataFrame({
        'Label': label_names,
        'Count': silence_label_pair_counts,
        'Probability': silence_label_pair_probabilities
    })

except Exception as e:
    emission_prob_df = None
    silence_emission_prob_df = None
    error_message = str(e)

emission_prob_df, silence_emission_prob_df, error_message if 'error_message' in locals() else "No error"



# Train the combined HMMs
def train_combined_hmms(num_iterations):
    # Initialize the letter and silence HMMs
    letter_HMMs = {letter: HMM(num_states=3, num_outputs=256) for letter in 'abcdefghijklmnopqrstuvwxyz' if letter not in ['k', 'q', 'z']}
    silence_HMM = HMM(num_states=5, num_outputs=256)

    # Initialize HMMs with starting probabilities
    for hmm in letter_HMMs.values():
        hmm.init_transition_probs( np.array([
    [0.8, 0.2, 0.0],
    [0.0, 0.8, 0.2],
    [0.0, 0.0, 0.8]
    ]))


    silence_HMM.init_transition_probs([0.25, 0.25, 0.25, 0.25, 0.00],
    [0.00, 0.25, 0.25, 0.25, 0.25],
    [0.00, 0.25, 0.25, 0.25, 0.25],
    [0.00, 0.25, 0.25, 0.25, 0.25],
    [0.00, 0.00, 0.00, 0.00, 0.75]) # replace with actual matrix


    # Combine the letter HMMs to form word HMMs
    combined_hmms = {word: initialize_combined_hmm(word, letter_HMMs, silence_HMM) for word in scripts}

    # The actual training loop
    for iteration in range(num_iterations):
        # Reset counts before each iteration
        for hmm in combined_hmms.values():
            hmm.reset_counters()

        # Update counts based on all training sequences
        for word, sequences in zip(scripts, label_sequences):
            for sequence in sequences:
                indices = [label_pair_counts[label] for label in sequence.split()]
                hmm = combined_hmms[word]
                alphas, betas, Q = hmm.forward_backward(indices)
                hmm.update_counters(alphas, betas, indices)

        # After processing all sequences, update HMM parameters
        for hmm in combined_hmms.values():
            hmm.normalize_counters()


    total_log_likelihood = sum(hmm.compute_log_likelihood(label_sequences, ...) for hmm in combined_hmms.values())
    return combined_hmms, total_log_likelihood


    log_likelihoods_over_time = []

    for iteration in range(num_iterations):
        word_log_likelihoods = defaultdict(float)

        for word, sequences in zip(scripts, label_sequences):
            indices = preprocess_sequences(sequences, label_to_index)
            hmm = combined_hmms[word]

            for sequence in indices:
                alphas, betas, Q = hmm.forward_backward(sequence)
                hmm.update_counters(alphas, betas, sequence)
                word_log_likelihoods[word] += hmm.compute_sequence_log_likelihood(alphas)

        total_log_likelihood = sum(word_log_likelihoods.values())
        log_likelihoods_over_time.append(total_log_likelihood)

        for hmm in combined_hmms.values():
            hmm.update_params()

        print(f"Iteration {iteration}: Total Log Likelihood = {total_log_likelihood}")

    # Plot the total log likelihood over iterations
    plt.plot(log_likelihoods_over_time, marker='o', label='Total Log Likelihood')
    plt.xlabel('Iteration')
    plt.ylabel('Log Likelihood')
    plt.title('Total Log Likelihood over Training Iterations')
    plt.legend()
    plt.show()

    return combined_hmms, total_log_likelihood

# Use this function to train your HMMs
num_iterations = 10  # This should be determined based on your convergence criteria
combined_hmms, total_log_likelihood = train_combined_hmms(num_iterations)

#Just an outline of the contrast system, does not work

import numpy as np
from sklearn.model_selection import train_test_split

# Function to load and preprocess label sequences from a file
def load_label_sequences(filename):
    with open(filename, 'r') as file:
        data = [line.strip().split() for line in file.readlines()[1:]]
    # Flatten the list if necessary, depending on your data structure
    flattened_data = [item for sublist in data for item in sublist]
    return flattened_data

# Function to load the scripts which are words read by speakers
def load_scripts(filename):
    with open(filename, 'r') as file:
        data = [line.strip() for line in file.readlines()[1:]]  # Skip the header
    return data

# Function to split data into training and held-out sets while preserving the distribution of words
def split_data(scripts, labels, test_size=0.2):
    numeric_labels = [int(label) for label in labels]
    return train_test_split(scripts, numeric_labels, test_size=test_size, random_state=42, stratify=scripts)

# Placeholder function to initialize HMMs for each word
def initialize_hmms(scripts, num_states_per_hmm, num_observations):
    # Initialize a dictionary to hold the HMM for each unique word
    unique_words = set(scripts)
    hmms = {word: {'transitions': np.full((num_states_per_hmm, num_states_per_hmm), 1.0 / num_states_per_hmm),
                   'emissions': np.full((num_observations, num_states_per_hmm), 1.0 / num_observations)}
            for word in unique_words}
    return hmms

# Placeholder function to run the forward-backward algorithm on the HMM for each word
def run_forward_backward(hmms, scripts, labels):
    # Run the forward-backward algorithm for each script/label pair and accumulate counts
    for script, label in zip(scripts, labels):
        hmm = hmms[script]
        # Here you would need to replace this with your actual forward-backward implementation
        pass

# Placeholder function to update HMM parameters from accumulated counts
def update_hmm_parameters(hmms):
    # Normalize and update the transition and emission matrices for each HMM
    for hmm in hmms.values():
        pass  # Replace with actual update logic

# Placeholder function to evaluate the model on held-out/test set
def evaluate_accuracy(hmms, scripts, labels):
    correct_predictions = 0
    total_predictions = len(labels)
    for script, label in zip(scripts, labels):
        hmm = hmms[script]
        # Replace with actual prediction using the HMM and comparison with label
        correct_predictions += 1  # Dummy implementation
    return correct_predictions / total_predictions

# Function to train HMMs until convergence on the held-out data accuracy
def train_hmms_until_convergence(train_scripts, train_labels, held_out_scripts, held_out_labels, hmms):
    prev_accuracy = 0.0
    current_accuracy = -1.0
    iteration = 0
    while current_accuracy > prev_accuracy:
        iteration += 1
        run_forward_backward(hmms, train_scripts, train_labels)
        update_hmm_parameters(hmms)
        prev_accuracy = current_accuracy
        current_accuracy = evaluate_accuracy(hmms, held_out_scripts, held_out_labels)
        print(f"Iteration {iteration}, Accuracy: {current_accuracy}")
    return iteration

# Path to the data files
script_file_path = 'clsp.trnscr'
label_file_path = 'clsp.trnlbls'

# Load and preprocess the data
scripts = load_scripts(script_file_path)
labels = load_label_sequences(label_file_path)

# Split into training and held-out sets
train_scripts, test_scripts, train_labels, test_labels = split_data(scripts, labels)

# Initialize your HMMs here with the appropriate parameters
num_states_per_hmm = 3  # Example, as each letter has a 3-state HMM
num_observations = 256  # Example, as there are 256 clusters/labels
hmms = initialize_hmms(train_scripts, num_states_per_hmm, num_observations)

# Train HMMs and get the iteration count when convergence happened
N_star = train_hmms_until_convergence(train_scripts, train_labels, test_scripts, test_labels, hmms)

