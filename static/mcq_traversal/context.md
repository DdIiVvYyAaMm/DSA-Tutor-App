# Tree Traversals

Traversal in binary trees refers to the process of visiting all the nodes in the tree in a specific order.
There are different ways to traverse a tree systematically.

## Common Traversal Methods:

### **Preorder Traversal** 
- Visit the root node.
- Traverse the left subtree in preorder.
- Traverse the right subtree in preorder.
- The sequence for a node N follows the pattern: N, Left, Right.

### **Inorder Traversal**
- Traverse the left subtree in inorder.
- Visit the root node.
- Traverse the right subtree in inorder.
- The sequence for a node N follows the pattern: Left, N, Right.
- This traversal is particularly useful for binary search trees because it produces the nodes in sorted order.

### **Postorder Traversal**
- Traverse the left subtree in postorder.
- Traverse the right subtree in postorder.
- Visit the root node.
- The sequence for a node N follows the pattern: Left, Right, N.

### **Level Order Traversal** 
Also known as breadth-first traversal, nodes are visited level by level starting from the root. All nodes at a given depth are visited before moving on to nodes at the next depth level. This traversal uses a queue data structure to manage the nodes as they are visited.

## A Visual Example of an Inorder Traversal

![Inorder Traversal Example](static/mcq_traversal/images/inorder_traversal.gif)