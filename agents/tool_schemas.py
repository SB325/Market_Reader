from typing import Annotated
from pydantic import BaseModel, Field, SkipValidation
import pdb

class news_article_model(BaseModel):
    company_name: Annotated[str, Field(SkipValidation, description="a company name", arbitrary_types_allowed=True)]
    created: Annotated[str, Field(SkipValidation, description="date that the news article was created", arbitrary_types_allowed=True)]
    title: Annotated[str, Field(SkipValidation, description="title of the news article", arbitrary_types_allowed=True)]
    teaser: Annotated[str, Field(SkipValidation, description="preview of the body of the news article", arbitrary_types_allowed=True)]
    body: Annotated[str, Field(SkipValidation, description="body of the news article", arbitrary_types_allowed=True)]

class technical_model(BaseModel):
    company_name: Annotated[str, Field(SkipValidation, description="a company name", arbitrary_types_allowed=True)]
    open: Annotated[str, Field(SkipValidation, description="price per share at market open", arbitrary_types_allowed=True)]
    high: Annotated[str, Field(SkipValidation, description="highest price per share of the day", arbitrary_types_allowed=True)]
    low: Annotated[str, Field(SkipValidation, description="lowest price per share of the day", arbitrary_types_allowed=True)]
    close: Annotated[str, Field(SkipValidation, description="price per share at market close", arbitrary_types_allowed=True)]

class fundamentals_model(BaseModel):
    company_name: Annotated[str, Field(SkipValidation, description="a company name", arbitrary_types_allowed=True)]
    filing_date: Annotated[str, Field(SkipValidation, description="date that filing was submitted", arbitrary_types_allowed=True)]
    form_description: Annotated[str, Field(SkipValidation, description="SEC document description", arbitrary_types_allowed=True)]
    filing_body: Annotated[str, Field(SkipValidation, description="content of the SEC filing", arbitrary_types_allowed=True)]

class company_id_model(BaseModel):
    company_name: Annotated[str, Field(SkipValidation, description="a company name", arbitrary_types_allowed=True)]
    ticker: Annotated[str, Field(SkipValidation, description="company ticker symbol that is unique for each company", arbitrary_types_allowed=True)]
    cik: Annotated[str, Field(SkipValidation, description="company cik symbol that is unique for each company", arbitrary_types_allowed=True)]
    exchange: Annotated[str, Field(SkipValidation, description="equities exchange that the company is listed under", arbitrary_types_allowed=True)]
    sicDescription: Annotated[str, Field(SkipValidation, description="the industry that the company does business in", arbitrary_types_allowed=True)]
    ownerOrg: Annotated[str, Field(SkipValidation, description="the sector that the company does business in", arbitrary_types_allowed=True)]
    formerNames: Annotated[str, Field(SkipValidation, description="former names that the company was referred to as along with the dates that those names were active", arbitrary_types_allowed=True)]

class business_address_model(BaseModel):
    cik: Annotated[str, Field(SkipValidation, description="company cik symbol that is unique for each company", arbitrary_types_allowed=True)]
    street1: Annotated[str, Field(SkipValidation, description="street address line 1", arbitrary_types_allowed=True)]
    street2: Annotated[str, Field(SkipValidation, description="street address line 2", arbitrary_types_allowed=True)]
    city: Annotated[str, Field(SkipValidation, description="city that the business is located in", arbitrary_types_allowed=True)]
    stateOrCountry: Annotated[str, Field(SkipValidation, description="2 character u.s.state identifier or external province identifier", arbitrary_types_allowed=True)]
    stateOrCountryDescription: Annotated[str, Field(SkipValidation, description="2 character u.s. state identifier or full foreign location string", arbitrary_types_allowed=True)]
    zipCode: Annotated[str, Field(SkipValidation, description="zip code of business location", arbitrary_types_allowed=True)]