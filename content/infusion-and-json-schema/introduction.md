Title: Infusion and JSON Schema...
Date: 2017-05-16 10:00
Category: Code
Tags: JSON Schema
Status: Draft
Slug: infusion-and-json-schema
Author: Tony Atkins <tony@raisingthefloor.org>
Summary: An overview of the combined use of Infusion and JSON Schema and the conversation to date.

# Introduction

In recent discussions in the offsite and in previous PCP API meetings, we have been talking through a few different strategies for validating settings (and component options in general) using [JSON Schemas](http://json-schema.org/).  In this collection of articles, I will attempt to summarise a range of approaches.  My hope is that with clearer examples, we can make an informed decision about which choices make sense to proceed with.  I say "choices" because I believe, as with so many of our choices ([webdriver](https://github.com/SeleniumHQ/selenium/tree/master/javascript/node/selenium-webdriver) vs. [Testem](https://github.com/testem/testem), for example), there may be room for more than one approach within the larger community.

# Why are we even talking about this?

There are a few specific projects currently under development where the ability to validate options using JSON Schemas is directly relevant:

1. [The UI portion of the PCP API](https://issues.gpii.net/browse/UX-180) that Bern, Javi and others are working on.
2. [The "Dev PMT" Steve is working on.](https://github.com/sgithens/gpii-devpmt), where settings are input based on the associated JSON Schema (for now, just the overall "type").
3. [The "Live Registries"](https://github.com/the-t-in-rtf/gpii-live-registries), which proposes breaking down the existing solutions data in universal into a separate repository with versioned releases.

In addition, there have been previous efforts within the community to use JSON Schemas, for example:

1. JSON Schemas are used within the [First Discovery Server](https://github.com/GPII/first-discovery-server/blob/master/src/js/configUtils.js#L41) to validate component options.
2. The [gpii-json-schema library)](https://github.com/GPII/gpii-json-schema) is used within the Unified Listing and PTD to perform both client and server-side validation of model data.

Between our legacy and ongoing work, we have a need to:

1. Validate user input and give appropriate feedback.
2. Validate component options.
3. Generate UIs based on schemas.

# So where do we go from here?

Among other things, we still need at least tentative agreement regarding:

1. How we can reuse and extend schema validation rules.
2. How to provide end-user-friendly feedback, both regarding the purpose of a field (instructions), and feedback when data is invalid (errors).

I will attempt to summarise the approaches suggested to date for each of these in subsequent sections, which are intended to be read in no particular order:

* [Reusing and Extending Schema Rules]({filename}reusing-and-extending.md)
* [Providing End User Feedback]({filename}end-user-feedback.md)

Within each of these, I will attempt to demonstrate a range of approaches:

1. A more "component centric" approach, where schema information is written directly in component options.
2. A more "schema centric" approach, where common schema information is stored in external files.
3. Options for working somewhere between the two, for example, writing inline schemas that link to external files as needed.

There will be a summary in each of the above sections, but this document will not attempt to present any decisions or make strong recommendations.  Rather, it is intended to serve as a starting point for the next few rounds of conversation.
