import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { buildSubgraphSchema } from '@apollo/subgraph';
import gql from 'graphql-tag';

const typeDefs = gql`
  type Hotel @key(fields: "id") {
    id: ID!
    name: String
    city: String
    stars: Int
  }

  type Query {
    hotelsByIds(ids: [ID!]!): [Hotel]
  }
`;

// TODO: заменить на REST/gRPC-вызов к hotel-сервису монолита
const hotels = [
  { id: 'h1', name: 'Grand Hotel', city: 'Seoul', stars: 5 },
  { id: 'h2', name: 'Busan Resort', city: 'Busan', stars: 4 },
  { id: 'h3', name: 'Daegu Inn', city: 'Daegu', stars: 3 },
];

const resolvers = {
  Hotel: {
    __resolveReference: async (ref) => {
      // Разрешение ссылки из booking-subgraph по ID
      return hotels.find((h) => h.id === ref.id);
    },
  },
  Query: {
    hotelsByIds: async (_, { ids }) => {
      return ids.map((id) => hotels.find((h) => h.id === id)).filter(Boolean);
    },
  },
};

const server = new ApolloServer({
  schema: buildSubgraphSchema([{ typeDefs, resolvers }]),
});

startStandaloneServer(server, {
  listen: { port: 4002 },
}).then(() => {
  console.log('✅ Hotel subgraph ready at http://localhost:4002/');
});
