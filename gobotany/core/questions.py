from gobotany.core.models import (Character, Taxon, TaxonCharacterValue)

def _is_length(short_name):
    """Detect whether a filter is a numeric length filter."""
    return (short_name.find('length') > -1 or
            short_name.find('width') > -1 or
            short_name.find('height') > -1 or
            short_name.find('thickness') > -1 or
            short_name.find('diameter') > -1)

def _number_of_answers(species_query_set, question_short_name):
    """Return the number of answers for a question for the given species.
    This has the effect of excluding answers that are no longer available
    to the user, i.e. are disabled and grayed out.
    """
    species_ids = species_query_set.values_list('id', flat=True)
    number_of_answers = 0
    if not _is_length(question_short_name):
        number_of_answers = TaxonCharacterValue.objects.filter(
            character_value__character__short_name=question_short_name,
            taxon__in=species_ids
        ).values_list(
            'character_value__value_str', flat=True
        ).distinct().count()
    return number_of_answers


def get_questions(request, pile):
    """Returns a list of questions for a plant subgroup (pile).
    A possible replacement for using piles_characters for choosing
    the next best questions. This takes the current filtering
    state into account to return questions with more than one
    non-zero-count choices first: these are questions the user can
    immediately use without first clearing some filter selections.
    """
    # Start with the list of characters for the plant subgroup.
    characters = Character.objects.filter(pile=pile)

    # Filter on any character groups that were specified.
    character_group_ids = set(
        int(n) for n in request.GET.getlist('character_group_id')
        )
    if len(character_group_ids) > 0:
        characters = characters.filter(
            character_group__in=character_group_ids
        )

    # Order by ease of observability. (lower number = easier)
    characters = characters.order_by('ease_of_observability')

    # Exclude any characters for questions already listed on the page.
    listed_questions = set(request.GET.getlist('exclude'))
    if len(listed_questions) > 0:
        characters = characters.exclude(
            short_name__in=listed_questions
        )

    # Build a list of candidate questions to be checked in order.
    candidate_questions = characters.values('character_group__id',
        'short_name', 'friendly_name', 'ease_of_observability')

    # Get the species that represent the current filtering state.
    species_ids = request.GET.get('species_ids', '')
    species_ids = species_ids.split('_') if species_ids.strip() else ()
    filtered_species = Taxon.objects.filter(id__in=species_ids)

    # Build a list of the specified number of best questions (or a default
    # number), in order of ease of observability.
    number_of_best_questions = int(request.GET.get('choose_best') or 3)
    best_questions = []
    for question in candidate_questions:
        short_name = question['short_name']
        if _is_length(short_name):
            # Allow a length-filter question to go on as a "best" question.
            question['best'] = True
        else:
            # For text-filter questions, get the number of currently
            # available answers. These are answers that appear on the
            # page as enabled and selectable, with a non-zero count in
            # parentheses.
            number_of_answers = _number_of_answers(filtered_species,
                                                   short_name)
            # The question is marked "best" if it has more than one
            # currently available answer.
            question['best'] = (number_of_answers > 1)

        if question['best'] == True:
            best_questions.append(question)
        if len(best_questions) >= number_of_best_questions:
            break

    # If there are leftover slots in the best-questions list that is to
    # be returned, then not enough of the candidate questions qualified
    # as "best" questions. Fill any remaining slots with questions that
    # did not qualify, also in order of ease of observability.
    if len(best_questions) < number_of_best_questions:
        for question in candidate_questions:
            if ((not question.has_key('best')) or
                (question.has_key('best') and question['best'] == False)):
                best_questions.append(question)
            if len(best_questions) >= number_of_best_questions:
                break

    # For testing/debugging
    #response = ({
    #    'answered_questions': answered_questions,
    #    'candidate_questions': candidate_questions,
    #    'best_questions': best_questions,
    #    })
    response = [question['short_name'] for question in best_questions]

    return response
