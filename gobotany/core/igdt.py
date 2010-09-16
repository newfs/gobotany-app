'''An implementation of Information Gain and Decision Tree compilation.
Much of the implementation was pulled from the (assumed) public domain
code located at:
  http://onlamp.com/python/2006/02/09/examples/dtree.tar.gz
  http://onlamp.com/pub/a/python/2006/02/09/ai_decision_trees.html?page=1
'''
import math
from collections import defaultdict

from gobotany.core.models import Character, TaxonCharacterValue

def compute_character_entropies(pile, species_list):
    """Find the most effective characters for narrowing down these species.

    The return value will be an already-sorted list of tuples, each of
    which looks like::

        (entropy, character_id)

    """
    # We start by fetching the character values for this pile (ignoring
    # "NA" values, since they really state that a character doesn't
    # apply to a species), and then selecting the TaxonCharacterValue
    # rows that match one of these character values with one of the
    # species given in `species_list`.

    character_values = pile.character_values.exclude(value_str='NA')
    taxon_character_values = TaxonCharacterValue.objects.filter(
            taxon__in=species_list, character_value__in=character_values)

    # Since Django's ORM will stupidly re-query the database if we ask
    # for the ".character_value" of one of these TaxonCharacterValue
    # objects, we put these character values in a dictionary by ID so
    # that we can get them more quickly ourselves.

    character_values_by_id = dict( (cv.id, cv) for cv in character_values )

    # To compute a character's entropy, we need to know two things:
    #
    # 1. How many species total are touched by that character's values.
    #    If a particular species is linked to two of the character's
    #    values ("this plant has blue flowers AND red flowers"), then
    #    the species still only gets counted once.
    #
    #    So we create a "character_species" dictionary that maps
    #    character IDs to species-ID sets, and count the length of each
    #    set of species IDs when we are done.
    #
    # 2. How many times each character value is used.  So we create a
    #    character_value_counts dictionary.
    #
    # Both of these data structures are populated very simply, by
    # iterating once across our taxon_character_values query.

    character_values = defaultdict(set)
    character_species = defaultdict(set)
    character_value_counts = defaultdict(int)

    for tcv in taxon_character_values:
        cv = character_values_by_id[tcv.character_value_id]
        character_values[cv.character_id].add(cv)
        character_species[cv.character_id].add(tcv.taxon_id)
        character_value_counts[cv] += 1

    # Finally, we are ready to compute the entropies!  We tally up the
    # value "n * log n" for each character value in a character, then
    # divide the result by the total number of species touched by that
    # character.  We also throw in to our result, just for good measure,
    # a "coverage" fraction indicating how many of the species we are
    # looking at are touched by each character.

    n = float(len(species_list))

    result = []
    for character_id in character_values:
        value_set = character_values[character_id]
        species_set = character_species[character_id]
        ne = _text_entropy(value_set, species_set, character_value_counts)
        entropy = ne / n
        coverage = len(species_set) / n
        result.append((character_id, entropy, coverage))

    return result


def _text_entropy(value_set, species_set, character_value_counts):
    """Compute the info-gain from choosing a value of a text character."""
    tally = 0.0
    for character_value in value_set:
        count = character_value_counts[character_value]
        tally += count * math.log(count, 2.)
    return tally


def compute_score(entropy, coverage, ease):
    """Our secret formula for deciding which characters are best!"""
    penalty = 10. * (1. - coverage)
    return entropy + penalty + 0.1 * ease


def rank_characters(pile, species_list):
    """Returns a list of (score, entropy, coverage, character), best first."""
    celist = compute_character_entropies(pile, species_list)
    result = []

    for character_id, entropy, coverage in celist:
        character = Character.objects.get(id=character_id)
        if character.value_type not in (u'TEXT', u'LENGTH'):
            continue  # skip non-textual filters
        ease = character.ease_of_observability
        score = compute_score(entropy, coverage, ease)
        result.append((score, entropy, coverage, character))

    result.sort()
    return result

# From here down is old, poorly written code to remove later.

class InformationTheoretic(object):

    def entropy(self, data, target_attr):
        """
        Calculates the entropy of the given data set for the target attribute.
        """
        val_freq = {}
        data_entropy = 0.0

        # Calculate the frequency of each of the values in the target attr
        for record in data:
            if record[target_attr] in val_freq:
                val_freq[record[target_attr]] += 1.0
            else:
                val_freq[record[target_attr]] = 1.0

        # Calculate the entropy of the data for the target attribute
        for freq in val_freq.values():
            data_entropy += (-freq / len(data)) * math.log(freq / len(data), 2)

        return data_entropy

    def gain(self, data, attr, target_attr):
        """
        Calculates the information gain (reduction in entropy) that would
        result by splitting the data on the chosen attribute (attr).
        """
        val_freq = {}
        subset_entropy = 0.0

        # Calculate the frequency of each of the values in the target attribute
        for record in data:
            if record[attr] in val_freq:
                val_freq[record[attr]] += 1.0
            else:
                val_freq[record[attr]] = 1.0

        # Calculate the sum of the entropy for each subset of records weighted
        # by their probability of occuring in the training set.
        for val in val_freq.keys():
            val_prob = val_freq[val] / sum(val_freq.values())
            data_subset = [record for record in data if record[attr] == val]
            subset_entropy += val_prob * self.entropy(data_subset, target_attr)

        # Subtract the entropy of the chosen attribute from the entropy of the
        # whole data set with respect to the target attribute (and return it)
        return (self.entropy(data, target_attr) - subset_entropy)


class DecisionTree(object):
    '''Decision tree maker.

    >>> lines = """
    ... Age, Education, Income, Marital Status, Purchase?
    ... 36 - 55, masters, high, single, will buy
    ... 18 - 35, high school, low, single, won't buy
    ... 36 - 55, masters, low, single, will buy
    ... 18 - 35, bachelors, high, single, won't buy
    ... < 18, high school, low, single, will buy
    ... 18 - 35, bachelors, high, married, won't buy
    ... 36 - 55, bachelors, low, married, won't buy
    ... > 55, bachelors, high, single, will buy
    ... 36 - 55, masters, low, married, won't buy
    ... > 55, masters, low, married, will buy
    ... 36 - 55, masters, high, single, will buy
    ... > 55, masters, high, single, will buy
    ... < 18, high school, high, single, won't buy
    ... 36 - 55, masters, low, single, will buy
    ... 36 - 55, high school, low, single, will buy
    ... < 18, high school, low, married, will buy
    ... 18 - 35, bachelors, high, married, won't buy
    ... > 55, high school, high, married, will buy
    ... > 55, bachelors, low, single, will buy
    ... 36 - 55, high school, high, married, won't buy
    ... """

    >>> lines = [x.strip() for x in lines.split('\\n') if x.strip()]
    >>> lines.reverse()
    >>> attributes = [attr.strip() for attr in lines.pop().split(",")]
    >>> target_attr = attributes[-1]
    >>> lines.reverse()

    >>> data = []
    >>> for line in lines:
    ...     data.append(dict(zip(attributes,
    ...     [datum.strip() for datum in line.split(",")])))

    >>> examples = data[:]
    >>> dt = DecisionTree(data, attributes, target_attr)
    >>> for item in dt.classify(examples):
    ...    print item
    will buy
    won't buy
    will buy
    won't buy
    will buy
    won't buy
    won't buy
    will buy
    won't buy
    will buy
    will buy
    will buy
    won't buy
    will buy
    will buy
    will buy
    won't buy
    will buy
    will buy
    won't buy

    '''

    def __init__(self, data, attribs, target_attr):
        self._ig = InformationTheoretic()
        self._treedata = self._create_decision_tree(data, attribs, target_attr)

    def classify(self, data):
        """
        Returns a list of classifications for each of the records in the data
        list as determined by the given decision tree.
        """
        return (self._get_classification(record)
                for record in data)

    def _majority_value(self, data, target_attr):
        """
        Creates a list of all values in the target attribute for each record
        in the data list object, and returns the value that appears in this
        list the most frequently.
        """
        data = data[:]
        return self._most_frequent([record[target_attr] for record in data])

    def _most_frequent(self, lst):
        """
        Returns the item that appears most frequently in the given list.
        """
        lst = lst[:]
        highest_freq = 0
        most_freq = None

        for val in self._unique(lst):
            if lst.count(val) > highest_freq:
                most_freq = val
                highest_freq = lst.count(val)

        return most_freq

    def _unique(self, lst):
        """
        Returns a list made up of the unique values found in lst.  i.e., it
        removes the redundant values in lst.
        """
        lst = lst[:]
        unique_lst = []

        # Cycle through the list and add each value to the unique list only
        # once.
        for item in lst:
            if unique_lst.count(item) <= 0:
                unique_lst.append(item)

        # Return the list with all redundant values removed.
        return unique_lst

    def _get_values(self, data, attr):
        """
        Creates a list of values in the chosen attribut for each record
        in data, prunes out all of the redundant values, and return
        the list.
        """
        data = data[:]
        return self._unique([record[attr] for record in data])

    def _choose_attribute(self, data, attributes, target_attr):
        """
        Cycles through all the attributes and returns the attribute with the
        highest information gain (or lowest entropy).
        """
        data = data[:]
        best_gain = 0.0
        best_attr = None

        for attr in attributes:
            gain = self._ig.gain(data, attr, target_attr)
            if (gain >= best_gain and attr != target_attr):
                best_gain = gain
                best_attr = attr

        return best_attr

    def _get_examples(self, data, attr, value):
        """
        Returns a list of all the records in <data> with the value of <attr>
        matching the given value.
        """
        data = data[:]
        rtn_lst = []

        if not data:
            return rtn_lst
        else:
            record = data.pop()
            if record[attr] == value:
                rtn_lst.append(record)
                rtn_lst.extend(self._get_examples(data, attr, value))
                return rtn_lst
            else:
                rtn_lst.extend(self._get_examples(data, attr, value))
                return rtn_lst

    def _get_classification(self, record, node=None):
        """
        This function recursively traverses the decision tree and returns a
        classification for the given record.
        """

        if node is None:
            node = self._treedata
        elif not isinstance(node, (dict, list)):
            return node

        attr = node.keys()[0]
        t = node[attr][record[attr]]
        return self._get_classification(record, t)

    def _create_decision_tree(self, data, attributes, target_attr):
        """
        Returns a new decision tree based on the examples given.
        """
        data = data[:]
        vals = [record[target_attr] for record in data]
        default = self._majority_value(data, target_attr)

        # If the dataset is empty or the attributes list is empty, return the
        # default value. When checking the attributes list for emptiness, we
        # need to subtract 1 to account for the target attribute.
        if not data or (len(attributes) - 1) <= 0:
            return default
        # If all the records in the dataset have the same classification,
        # return that classification.
        elif vals.count(vals[0]) == len(vals):
            return vals[0]
        else:
            # Choose the next best attribute to best classify our data
            best = self._choose_attribute(data, attributes, target_attr)

            # Create a new decision tree/node with the best attribute
            # and an empty dictionary object--we'll fill that up next.
            tree = {best: {}}

            # Create a new decision tree/sub-node for each of the values in the
            # best attribute field
            for val in self._get_values(data, best):
                # Create a subtree for the current value under the "best" field
                subtree = self._create_decision_tree(
                    self._get_examples(data, best, val),
                    [attr for attr in attributes if attr != best],
                    target_attr)

                # Add the new subtree to the empty dictionary object in our new
                # tree/node we just created.
                tree[best][val] = subtree

        return tree
