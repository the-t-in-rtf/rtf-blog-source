Title: Infusion and JSON Schemas, Part 2: Reuse
Date: 2017-05-16 10:00
Category: Code
Tags: JSON Schema
Status: Draft
Slug: infusion-and-json-schema-reuse
Author: Tony Atkins <tony@raisingthefloor.org>
Summary: A detailed comparison of the inheritance and reuse issues involved in using JSON Schemas to validate Infusion component options.

# Introduction

This page provides an overview of the mechanisms in Infusion and JSON Schema that support reuse and extension, and how each might be used to associate options blocks with validation rules.

For a general overview of the broader topic and use cases, please review the [{content}/infusion-and-json-schema/introduction.md](introduction).

# The Inheritance Mechanisms Provided by Infusion

## Options Merging

The first inheritance mechanism we should discuss is [options merging](http://docs.fluidproject.org/infusion/development/OptionsMerging.html) is the mechanism by which options are combined from one or more "parent" grades (and their "parents").


```javascript
"use strict";
var fluid = require("infusion");

fluid.defaults("my.awesome.grade", {
    gradeNames: ["fluid.component"],
    size: "medium",
    colors: ["red", "green"],
    rankings: {
        "cats": "rule",
        "dogs": "drool"
    }
});

fluid.defaults("my.awesome.extension", {
    gradeNames: ["my.awesome.grade"],
    size: "extra large",
    colors: ["blue"],
    material: "cotton",
    rankings: {
        "dogs": "also rule"
    }
});
```

Note that both shallow (`size`) and deep (`rankings.dogs`) values can be replaced, and that all types of values can be easily added (`material`).  There are some limitations when merging arrays.  In the above example, the merged value of `colors` becomes `["blue", "green"]`.  In practice, we have moved to using [prioritised](http://docs.fluidproject.org/infusion/development/Priorities.html) and namespaced maps instead of arrays in many places.  This makes it possible to selectively add and replace material, but also to control the ordering (something that maps themselves do not guarantee).  As we will see later, the issues surrounding the use of arrays in options are directly relevant when we talk about portions of the JSON Schema standard (`required`, `allOf`, `anyOf`) that are represented as arrays.

It is possible to [indicate that particular options should not be merged at all](http://docs.fluidproject.org/infusion/development/OptionsMerging.html#structure-of-the-merge-policy-object), but this would greatly reduce the options for reuse and extension, as grades would have to completely redefine the schema to change it.  Although we may choose to disable options merging for schemas, for the rest of this section we will explore what is possible if we extend and reuse schema material in combination with options merging.

## IoC References and Options Distribution

[IoC references](http://docs.fluidproject.org/infusion/development/IoCReferences.html
) are a means of referring to another option.  Used on their own, they provide an easy way of exposing the same options in multiple places, as in the following example:

```javascript
fluid.defaults("my.ioc.parent", {
    gradeNames: ["fluid.modelComponent"],
    model: {
        parentVar: "is set"
    },
    components: {
        child: {
            type: "fluid.modelComponent",
            options: {
                model: {
                    childVar: "{parent}.model.parentVar"
                }
            }
        }
    }
});
```
This type of operation is duplicative, i.e. both the parent and child can see the same variable.  When we talk about reusing and reorganizing schemas, we will need some way to relocate options, to change their location.  A key mechanism that supports this is [options distribution](http://docs.fluidproject.org/infusion/development/IoCSS.html#distributeoptions-format).  Through the use of the `removeSource` option, it is possible to relocate options, as shown in the following example:

```javascript
fluid.defaults("my.disorganized.grade", {
    country: "Freelandia",
    address: {
        "street": "123 Main Street."
    }
});

fluid.defaults("my.reorganized.grade", {
    gradeNames: ["my.disorganized.grade"],
    distributeOptions: {
        source: "{that}.options.country",
        target: "{that}.options.address.country",
        removeSource: true
    }
});
```

We will demonstrate some practical examples of using this to reorganize existing material in the third set of examples below.

# The Inheritance Mechanisms Provided by JSON Schema

The JSON Schema standard provides two key mechanisms to support reuse.  

## The `$ref` keyword

A `$ref` keyword is a URI (full or partial) that points to validation rules elsewhere.  Although these URIs can point to material in another schema, for the purposes of this discussion, I will demonstrate the use of internal references.

```json
{
  "$schema": "http://json-schema.org/schema#",
  "definitions": {
    "email": {
      "type": "string",
      "format": "email"
    }
  },
  "properties": {
    "email": {
      "$ref": "#/definitions/email"
    }
  }
}
```

The property `email` uses its `$ref` keyword to indicate that it is defined elsewhere.  As with HTML anchors, the `#/` at the beginning of the URI indicates a link relative to the root of the current context, i.e. this schema.  Although it is by no means required, in my own work, I tend to use the above pattern to support reuse, general definitions that can be referred to both within the schema, and from other documents.

These references can be used circularly.  Let's assume we're defining a "person" record, and that we might want to (within that record) describe other people related to a given person.  For the purposes of brevity, I will avoid the definitions pattern used above.

```json
{
  "$schema": "http://json-schema.org/schema#",  
  "properties": {
    "family": { "type": "string"},
    "middle": { "type": "string"},
    "given": { "type": "string"},
    "email": { "type": "string", "format": "email"},
    "relatives": {
      "type": "array",
      "items": { "$ref": "#", "required": ["family", "given"]}
    }
  },
  "required": ["family", "given", "email"]
}
```
  
First, we use `$ref` to indicate that this [array](https://spacetelescope.github.io/understanding-json-schema/reference/array.html) contains one or more other people. `#` in this context means that all definitions from the root of the schema down apply here.  So, for example, our `relatives` can also have `relatives`.

We also override the `required` keyword to indicate that for `relatives`, only the family and given name are required.  In JSON Schemas, directly overriding an array value like `required`, `anyOf`, `allOf` completely replaces its previous value. We will see examples of how this can be avoided for `anyOf` and `allOf` in later examples, but as `required` is a basic control we are likely to use often, I will use that in later examples of working with arrays.

## The `$id` keyword

The second mechanism that supports reuse is the `$id` keyword, which provides a means of naming the path to a portion of a schema.  The `$id` keyword can be used to provide shortcuts to a deep path within a schema, comparable to a named anchor.  

First, `$id` can (and should) be used for the root of the schema itself:

```json
{
  "$schema": "http://json-schema.org/schema#",
  "$id": "mySchema.json"
}
```

In practice, I tend to store schemas in a single directory, and have the `$id` match the filename, but we have many options for using whatever URI conventions we wish.  We are not constrained by what file the material is store in, where (or whether) it is hosted.  We do however need to make the validator aware of the schema that contains the ID before it is asked to resolve a URI that references it.

So, beyond simply identifying the schema, the primary purpose of the `$id` field is to give us a clear way to address schema material from a URI used with a `$ref` keyword.  Let's look at a simplified version of the first example above.

```json
{
  "$schema": "http://json-schema.org/schema#",
  "definitions": {
    "email": {
      "$id": "email",
      "type": "string",
      "format": "email"
    }
  },
  "properties": {
    "email": {
      "$ref": "#email"
    }
  }
}
```

Regardless of where the rules that define the `email` field are located, we can always refer to it using the `$ref` `#email`.

We can also include path information on the right side of the hash tag, which allows us to organize the URI space a bit:

```json
{
  "$schema": "http://json-schema.org/schema#",
  "definitions": {
    "pet-animal": {
      "$id": "#/animals/pet",
      "type": "string",
      "description": "A companion animal."
    },
    "pet-verb": {
      "$id": "#/verbs/pet",
      "type": "boolean",
      "description": "Is it a good idea to handle the companion animal?"
    }
  }
}
```

The `$id` keyword can also include information on the left side of the hash sign, which form a kind of "virtual" schemas, as shown here:


```json
{
  "$schema": "http://json-schema.org/schema#",
  "definitions": {
    "pet-animal": {
      "$id": "animals.json#pet",
      "type": "string",
      "description": "A companion animal."
    },
    "pet-verb": {
      "$id": "http://bogus.host/schemas/verbs.json#pet",
      "type": "boolean",
      "description": "Is it a good idea to handle the companion animal?"
    }
  }
}
```

Once a validator has been made aware of the above, there are in essence two additional known URIs for schemas.  The first ("animals.json") is in the same base namespace as the enclosing schema.  The second ("verbs.json") includes hostname and path information on the left side.  At least for these two fiels, AJV will use the information provided above instead of attempting to retrieve the schema from the portion of the URI on the left side of the hash sign.

This offers interesting possibilities for working with early draft updates to schemas locally, but also highlights how important it is that we have control over and trust all of the schemas we load.  Any schema can in essence take control of any URI it likes, regardless of where it is actually stored.

# Examples

So, I have tried to give a partial overview of two pretty complex technologies above, identifying the tools that I see as being helpful in achieving practical goals.  Let's look at some of these practical goals with specific examples.  For each example, I will illustrate the following:

1. What we can accomplish purely with inline schemas and options merging ("inline").
2. What we can accomplish purely with external JSON Schema files ("external").
3. What we can accomplish with a combination of the two ("hybrid").

## Example Set 0: Our Initial Schema, Component, and Starting Assumptions

### "Inline"

For all "inline" examples, I will assume a base grade called `gpii.schema.inline`, that looks like the following:

```javascript
fluid.defaults("gpii.schema.inline", {
    gradeNames: ["fluid.component"],
    schema: {
        "$schema": "http://json-schema.org/schema#",
        "$id": "schemaComponent.json#",
        "properties": {
            "schema": {
                "$id": "#/options/schema",
                "$ref": "http://json-schema.org/schema#"
            }
        },
        "required": ["schema"]
    }
});
```

All we are saying here is that we must have a `schema` option, and that it must be valid according to the (currently draft v6) standard located at `http://json-schema.org/schema#`, which is a real URL that we can download the standard from.

I have added `$id` values in the above, and wanted to point out a few things.  First, the path to the `schema` keyword is not a recommendation.  Rather, it is an example of the flexibility we have.  Even though we must use `definitions` and `properties` when defining schemas, we are not required to use those in our URIs if we feel like `options` are a better fit.

This approach has key advantages in that it is immediately familiar to Infusion developers, and that only one chain of inheritance (from parent grades) needs to be managed.

### "External"

Although we have range of options, the hardest form of "external" schemas would simply use a URI to refer to a schema.  The schema associated with the base grade for the "external" strategy would look slightly different:

```json
{
  "$schema": "http://json-schema.org/schema#",
  "$id": "schemaComponent.json#",
  "properties": {
    "schema": {
      "$id": "#/options/schema",
      "type": "string",
      "format": "uri"
    }
  },
  "required": ["schema"]
}
```

The component options might look something like:

```javascript
fluid.defaults("gpii.schema.external", {
    gradeNames: ["fluid.component"],
    schema: "schemaComponent.json#"
});
```
This approach requires us to either make the validator aware of one or more "core" schemas, or to host them somewhere they can be retrieved.  We must also define a new schema that extends the base schema, i.e. we must manage two chains of inheritance.

### "Hybrid"

In the "hybrid" approach, we use external files as needed, for example:

1. When we have a set of "common" definitions that it would be convenient to represent externally.
2. When we encounter a situation where simple options merging cannot accomplish the desired goal (or when it accomplishes the goal in a way that is overly cumbersome).

Although we should discuss where to draw the line, for the purposes of illustration, let's assume that the base grade itself uses an external schema, which looks like the "inline" schema's contents:

```json
{
  "$schema": "http://json-schema.org/schema#",

  "$id": "schemaComponent.json#",
  "properties": {
    "schema": {
      "$id": "#/options/schema",
      "$ref": "http://json-schema.org/schema#"
    }
  },
  "required": ["schema"]
}
```

The component might look like:

```javascript
fluid.defaults("gpii.schema.hybrid", {
    gradeNames: ["fluid.component"],
    schema: {
        "$ref": "schemaComponent.json#"
    }    
});
```
This approach still requires us to either make the validator aware of one or more "core" schemas, or to host them somewhere they can be retrieved.  However, simple options merging now cooperates better with JSON Schema inheritance.  As long as we do not redefine the top-level `$ref` keyword within the schema, we inherit the underlying validation rules.

## Example Set 1: Adding a New Field

### "Inline"

A grade following the "inline" strategy might add a single field as follows:

```javascript
fluid.defaults("gpii.schema.inline.example1", {
    gradeNames: ["gpii.schema.inline"],
    schema: {
        "properties": {
            "field1": { "type": "string" }
        },
        "required": ["schema", "field1"]
    },
    field1: "default"
});
```

Simple options merging would ensure that the new property is added, and we can similarly merge an associated definition if we wish to work in that way.  Note that because of the way in which arrays are merged, we must include any material from the base `required` keyword that we wish to preserve.  We must also ensure that our entry for `required` is at least as long as any base grade, otherwise we will end up with a mixture of our required fields and remaining fields from base grades with a longer set of `required` fields.


### "External"

Following the "external" strategy, before we can write our new component, we need to 
make a new schema, or add an entry to an existing schema that is loaded ahead of time, as in:

```json
{
    "$schema": "http://json-schema.org/schema#",
    "$ref": "externalSchema.json#",
    "$id": "myUniqueSchema.json#",
    "properties": {
      "field1": { "type": "string" }
    },
    "required": ["schema", "field1"]
}
```
Like the "inline" example, we must completely redefine the `required` keyword in the schema.  Unlike the "inline" example, it does not matter whether there are zero or a thousand entries in our base schema.

The associated component might look like:

```javascript
fluid.defaults("gpii.schema.external.example1", {
    gradeNames: ["fluid.component"],
    schema: "myUniqueSchema.json#",
    field1: "default"
});
```

### "Hybrid"

```javascript
fluid.defaults("gpii.schema.hybrid.example1", {
    gradeNames: ["gpii.schema.hybrid"],
    schema: {
        "properties": {
            "field1": { "type": "string" }
        },
        "required": ["schema", "field1"]
    },
    field1: "default"
});
```

Note that this is nearly identical to the "inline" example.

## Example Set 2: Making a Required Field Optional

Let's build on the previous examples, and assume we want to make derived component that does not require `field1`.

### "Inline"

As we cannot remove an array entry using options merging, we need to abstract out a "base" grade, then make the "required" field unique to a specific grade, as in the following example:

```javascript
fluid.defaults("gpii.schema.inline.example1.base", {
    gradeNames: ["gpii.schema.inline"],
    schema: {
        "properties": {
            "field1": { "type": "string" }
        }
    },
    field1: "default"
});

fluid.defaults("gpii.schema.inline.example1", {
    gradeNames: ["gpii.schema.inline.example1.base"],
    schema: {
        "required": ["schema", "field1"]
    }
});


fluid.defaults("gpii.schema.inline.example2", {
    gradeNames: ["gpii.schema.inline.example1"]
});
```

With that, our derived grade can extend the "base" grade and avoid requiring `field1`.

### "External"

In JSON Schema, an array value with the same name completely replaces what was there previously.  We can use the `$ref` keyword to extend an existing schema, and then override the value of the `required` keyword.

```json
{
    "$schema": "http://json-schema.org/schema#",
    "$ref": "myUniqueSchema.json#",
    "$id": "myUniqueSchema2.json#",
    "required": ["schema"]
}
```

Note that as in all previous examples, we must explicitly preserve the "schema" requirement.  Once we've created the schema, our component must both extend and replace the schema option for the parent grade, as in:

```javascript
fluid.defaults("gpii.schema.external.example2", {
    gradeNames: ["gpii.schema.external.example1"],
    schema: "myUniqueSchema2.json#"
});
```

### "Hybrid"

As in the "inline" approach, the "hybrid" approach also requires abstracting out a base grade that lacks the "required" option, and then deriving from that.

## Example Set 3: Reusing Existing Definitions within a Larger Structure

Thus far we have looked at individual blocks of options, which can be represented as a single component.  We also commonly works with "sets of options", for example a preference set that contains values for multiple individual settings, or a "capabilities" block, that describes multiple settings a solution supports.

### "Inline"

In the inline method, groups of schema-validated options are represented as individual subcomponents, as in 
the following example.  

```javascript
fluid.defaults("my.enclosing.grade", {
    gradeNames: ["gpii.schema.inline.enclosing"],
    enclosingOption1: true,
    components: {
        enclosed1: {
            type: "gpii.schema.inline.enclosed1"
        },
        enclosed2: {
            type: "gpii.schema.inline.enclosed2"
        }
    }
})
```

In this approach, from the enclosing component we can use tools like [`fluid.queryIoCSelector`](https://github.com/fluid-project/infusion/blob/master/src/framework/core/js/FluidIoC.js#L378)
to pick out schema validated components from other required components (for example, a shared validator instance).  This
can also be used to give an enclosing grade control over which particular classes of child grades it chooses to perform
a given action on.  There are no mechanisms for controlling the number of child grades that are required.

### "External"

The JSON Schema standard provides the ability to define arrays containing material that matches either local definitions
or a reference to an external schema, as shown in the following example:

```json
{
    "$schema": "http://json-schema.org/schema#",
    "$id": "myWrenchSet.json#",
    "properties":{
      "wrenches": {
        "type": "array",
        "items": {
          "$ref": "myWrench.json#"
        },
        "minItems": 1,
        "maxItems": 10
      }
    },
    "required": ["wrenches"]
}
```

We have the ability to indicate what type(s) of material we accept and how many items.