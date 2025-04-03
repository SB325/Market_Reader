# imports
import pdb
import re

class TitleFilter():
    threshold: float
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def get_figures(self, string: str):
        dollar_signs = [cnt for cnt, s in enumerate(string) if '$' in s]
        if len(dollar_signs)<2:
            return None
        figures = [float(string[dollar_signs[cnt]+1:dollar_signs[cnt]+5]) for cnt,_ in enumerate(dollar_signs)]
        pos = [False for cnt,_ in enumerate(dollar_signs) if '(' in string[dollar_signs[cnt]-1]]
        numbers = [-1 * fig for cnt, fig in enumerate(figures) if not pos[cnt]]

        return numbers
    
    def filter(self, title: str):
        ''' 
        TitleFilter.filter collects the title string, containing content like: 
        $X.XX up from $Y.YY 
        or 
        EPS($X.XX) Up From ($Y.YY) YoY
        parses it to look for before/after pairs ex:
        X.XX, Y.YY 
        
        The filter is the determination based on a % gain threshold of EPS or Sales etc.
        Titles accounting for a greater gain >threshold pass the filter.
        '''
        figure_pairs = self.get_figures(title)

        if figure_pairs:
            if 'Revenue' in title:
                return self.revenue_filter(figure_pairs)
            elif 'EPS' in title:
                return self.eps_filter(figure_pairs)
        else:
            return True, 0

    def eps_filter(self, eps_list: list):
        value = (eps_list[1]-eps_list[0])/eps_list[1]

        if self.threshold < value:
            return True, value
        else:
            return False, value

    def revenue_filter(self, revenue_list: list):
        value = (revenue_list[1]-revenue_list[0])/revenue_list[1]
        if self.threshold < value:
            return True, value
        else:
            return False, value

if __name__ == "__main__":
    sample = {'eps_sample': "TuHURA Biosciences FY24 EPS($1.21) Up From ($2.47) YoY",
              'eps_revenue_sample': "Generation Income Properties FY24 EPS ($1.64) Up From ($2.46) YoY; Revenue $9.51M up From $7.59M YoY",
              'revenue_sample': "LQR Hourse GGY24 Revenue $2.501M Up From $1.120M YoY"}

    tf = TitleFilter(0.5)

    selection = 'eps_sample'
    pass_fail,_  = tf.filter(sample[selection])

    outcome = 'Failed'

    if pass_fail[0]:
        outcome = 'Passed'

    print(f"Sample -{selection}- {outcome} with gain value of {pass_fail[1]}.")