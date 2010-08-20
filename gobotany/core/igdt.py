'''An implementation of Information Gain and Decision Tree compilation.
Much of the implementation was pulled from the (assumed) public domain
code located at:
  http://onlamp.com/python/2006/02/09/examples/dtree.tar.gz
  http://onlamp.com/pub/a/python/2006/02/09/ai_decision_trees.html?page=1
'''

import math


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
    >>> dt = DecisionTree()
    >>> tree = dt.create_decision_tree(data, attributes, target_attr)
    >>> classification = dt.classify(tree, examples)

    >>> for item in classification:
    ...    print item
    '''

    def __init__(self):
        self._ig = InformationTheoretic()

    def majority_value(self, data, target_attr):
        """
        Creates a list of all values in the target attribute for each record
        in the data list object, and returns the value that appears in this
        list the most frequently.
        """
        data = data[:]
        return self.most_frequent([record[target_attr] for record in data])

    def most_frequent(self, lst):
        """
        Returns the item that appears most frequently in the given list.
        """
        lst = lst[:]
        highest_freq = 0
        most_freq = None

        for val in self.unique(lst):
            if lst.count(val) > highest_freq:
                most_freq = val
                highest_freq = lst.count(val)

        return most_freq

    def unique(self, lst):
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

    def get_values(self, data, attr):
        """
        Creates a list of values in the chosen attribut for each record
        in data, prunes out all of the redundant values, and return
        the list.
        """
        data = data[:]
        return self.unique([record[attr] for record in data])

    def choose_attribute(self, data, attributes, target_attr):
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

    def get_examples(self, data, attr, value):
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
                rtn_lst.extend(self.get_examples(data, attr, value))
                return rtn_lst
            else:
                rtn_lst.extend(self.get_examples(data, attr, value))
                return rtn_lst

    def get_classification(self, record, tree):
        """
        This function recursively traverses the decision tree and returns a
        classification for the given record.
        """
        # If the current node is a string, then we've reached a leaf node and
        # we can return it as our answer
        if type(tree) == type("string"):
            return tree

        # Traverse the tree further until a leaf node is found.
        else:
            attr = tree.keys()[0]
            t = tree[attr][record[attr]]
            return self.get_classification(record, t)

    def classify(self, tree, data):
        """
        Returns a list of classifications for each of the records in the data
        list as determined by the given decision tree.
        """
        data = data[:]
        classification = []

        for record in data:
            classification.append(self.get_classification(record, tree))

        return classification

    def create_decision_tree(self, data, attributes, target_attr):
        """
        Returns a new decision tree based on the examples given.
        """
        data = data[:]
        vals = [record[target_attr] for record in data]
        default = self.majority_value(data, target_attr)

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
            best = self.choose_attribute(data, attributes, target_attr)

            # Create a new decision tree/node with the best attribute
            # and an empty dictionary object--we'll fill that up next.
            tree = {best: {}}

            # Create a new decision tree/sub-node for each of the values in the
            # best attribute field
            for val in self.get_values(data, best):
                # Create a subtree for the current value under the "best" field
                subtree = self.create_decision_tree(
                    self.get_examples(data, best, val),
                    [attr for attr in attributes if attr != best],
                    target_attr)

                # Add the new subtree to the empty dictionary object in our new
                # tree/node we just created.
                tree[best][val] = subtree

        return tree
